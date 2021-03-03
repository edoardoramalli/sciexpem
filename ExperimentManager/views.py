# Import django
from django.db import close_old_connections
from rest_framework.status import *
from rest_framework.response import Response
from rest_framework.views import APIView

# Import build-in
import sys

# Import Local
from SciExpeM.checkPermissionGroup import HasGroupPermission
import ExperimentManager
from SciExpeM import settings

# START LOGGER
# Logging
import logging

logger = logging.getLogger("ExperimentManager")
logger.addHandler(ExperimentManager.apps.logger_handler)
logger.setLevel(logging.INFO)


# END LOGGER


class ExperimentManagerBaseView(APIView):
    viewName = 'BaseView'
    paramsType = {}
    permission_classes = [HasGroupPermission] if settings.GROUP_ACTIVE else []

    def view_post(self, request):
        pass

    def view_get(self, request):
        pass

    # def get(self, request):
    #     try:
    #         params = dict(request.query_params)
    #         try:
    #             for par in self.paramsType:
    #                 self.__setattr__(par, self.paramsType[par](params[par][0]))
    #         except KeyError:
    #             return Response(status=HTTP_400_BAD_REQUEST,
    #                             data=self.viewName + ": KeyError in HTTP parameters. Missing parameter.")
    #
    #         return self.view_get()
    #
    #     except Exception:
    #         err_type, value, traceback = sys.exc_info()
    #         logger.info('Error ' + self.viewName + ': ' + str(err_type.__name__) + " : " + str(value))
    #         return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
    #                         data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
    #     finally:
    #         close_old_connections()

    def post(self, request):
        try:
            params = request.data
            try:
                for par in self.paramsType:
                    self.__setattr__(par, self.paramsType[par](params[par]))
            except KeyError:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": KeyError in HTTP parameters. Missing parameter.")

            return self.view_post(request=request)

        except Exception:
            err_type, value, traceback = sys.exc_info()
            logger.info('Error ' + self.viewName + ': ' + str(err_type.__name__) + " : " + str(value))
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                            data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
        finally:
            close_old_connections()
