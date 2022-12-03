from flask import request
from marshmallow import (
    Schema, 
    fields)
from urllib.parse import urlencode


class PaginationSchema(Schema):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/schemas/pagination.py
    """
    
    class Meta():
        ordered = True
    
    
    links = fields.Method(serialize='get_pagination_links')
    page = fields.Integer(dump_only=True)
    pages = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total = fields.Integer(dump_only=True, attribute='total') 


    @staticmethod
    def get_url(page):
        
        query_args = request.args.to_dict()
        query_args['page'] = page
        
        return '{}?{}'.format(request.base_url, urlencode(query_args))
    
    
    def get_pagination_links(self, paginated_object):
        
        pagination_link = {
            'first': self.get_url(page=1),
            'last': self.get_url(page=paginated_object.pages)
        }
        
        if paginated_object.has_prev:
            pagination_link['prev']  =self.get_url(page=paginated_object.prev_num)
        if paginated_object.has_next:
            pagination_link['next'] = self.get_url(page=paginated_object.next_num)
            
        return pagination_link
