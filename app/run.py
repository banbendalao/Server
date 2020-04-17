import os
import sys
from concurrent import futures

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict, Parse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 初始化配置
from app.config import server_config, logging

from app.grpc_server import route_pb2_grpc
from app.grpc_server.route_pb2 import AppStatus, ResponseList, DownloadInfo

from app.server.manager.data_manager import data_manager
from app.server.hubs.library.hub_list import hub_dict


class Greeter(route_pb2_grpc.UpdateServerRouteServicer):

    def GetAppStatus(self, request, context) -> AppStatus:
        request = MessageToDict(request, preserving_proto_field_name=True)
        hub_uuid = request['hub_uuid']
        if hub_uuid not in hub_dict:
            logging.warning(f"NO HUB: {hub_uuid}")
            return AppStatus(valid_hub_uuid=False)
        app_id: list = request['app_id']
        app_status = data_manager.get_app_status(hub_uuid, app_id)
        log_str = ""
        if not app_status['release_info']:
            log_str += "(empty)"
        logging.info(f"已完成单个请求 app_id: {app_id}{log_str} hub_uuid: {hub_uuid}")
        return ParseDict(app_status, AppStatus())

    def GetAppStatusList(self, request, context) -> ResponseList:
        request = MessageToDict(request, preserving_proto_field_name=True)
        hub_uuid = request["hub_uuid"]
        if hub_uuid not in hub_dict:
            logging.warning(f"NO HUB: {hub_uuid}")
            return {
                "response": [{"app_status": {"valid_hub_uuid": False}}]
            }
        app_id_list = request["app_id_list"]
        release_list = {
            "response": data_manager.get_response_list(hub_uuid, app_id_list)
        }
        logging.info(f"已完成批量请求 hub_uuid: {hub_uuid}（{len(app_id_list)}）")
        return ParseDict(release_list, ResponseList())

    def GetDownloadInfo(self, request, context) -> DownloadInfo:
        request = MessageToDict(request, preserving_proto_field_name=True)
        app_id_info = request["app_id_info"]
        hub_uuid = app_id_info["hub_uuid"]
        app_id = app_id_info["app_id"]
        asset_index = request["asset_index"]
        logging.info(f"请求下载资源 app_id: {app_id} hub_uuid: {hub_uuid}")
        download_info = data_manager.get_download_info(hub_uuid, app_id, asset_index)
        logging.info(f"回应下载资源: download_info: {download_info}")

        return ParseDict(download_info, DownloadInfo())


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=server_config.max_workers))
    route_pb2_grpc.add_UpdateServerRouteServicer_to_server(Greeter(), server)
    server.add_insecure_port(f'{server_config.host}:{server_config.port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
