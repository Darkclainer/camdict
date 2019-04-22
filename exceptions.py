class CamDictException(Exception):
    pass

class CannotParsePage(CamDictException): 
    pass

class UnknownIpa(CannotParsePage): 
    pass

class QueryException(CamDictException):
    pass

class QueryRefused(QueryException):
    pass

class QueryUnknownResponce(QueryException):
    pass
