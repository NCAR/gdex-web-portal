from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


from .matrix import Matrix 
class DataAccessAPIView(APIView):
   """
   API endpoint for retrieving dataset matrix information.
  
   This endpoint provides access to dataset download and access information
   including file locations, globus URLs, subset capabilities, and group data.
   """
  
   @extend_schema(
       parameters=[
           OpenApiParameter(
               name='dsid',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.PATH,
               description='Dataset ID (e.g., "ds123.456")',
               required=True
           ),
           OpenApiParameter(
               name='duser',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.QUERY,
               description='User identifier for personalized access',
               required=False
           ),
       ],
       responses={
           200: 'Matrix data with download options and access methods',
           404: 'Dataset not found',
           500: 'Server error'
       },
       description='Retrieve dataset matrix information including download options and access methods'
   )
   def get(self, request, dsid):
       """
       Retrieve matrix data for a specific dataset.
      
       Args:
           request: HTTP request object
           dsid: Dataset ID from URL path
          
       Returns:
           JSON response with matrix data or error information
       """
       try:
           duser = request.query_params.get('duser', '')
          
           if not dsid or not dsid.strip():
               return Response(
                   {'error': 'dsid parameter is required'},
                   status=status.HTTP_400_BAD_REQUEST
               )
          
           matrix = Matrix(dsid=dsid, duser=duser)
          
           matrix_data = matrix.to_json2()
          
           if 'matrix' in matrix_data and 'error' in matrix_data['matrix']:
               error_info = matrix_data['matrix']['error']
              
               if error_info.get('header') == 'No Public Access':
                   return Response(
                       matrix_data,
                       status=status.HTTP_403_FORBIDDEN
                   )
               elif error_info.get('header') == 'Server Error':
                   return Response(
                       matrix_data,
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR
                   )
               else:
                   return Response(
                       matrix_data,
                       status=status.HTTP_400_BAD_REQUEST
                   )
          
           return Response(matrix_data, status=status.HTTP_200_OK)
          
       except Exception as e:
           return Response(
               {
                   'matrix': {
                       'error': {
                           'header': 'Server Error',
                           'message': 'An unexpected error occurred',
                           'module': 'MatrixAPIView'
                       }
                   }
               },
               status=status.HTTP_500_INTERNAL_SERVER_ERROR
           )