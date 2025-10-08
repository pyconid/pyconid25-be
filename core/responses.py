from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response


class HttpResponseAbstract(metaclass=ABCMeta):
    @abstractmethod
    def response(self) -> Union[JSONResponse, Response, None]:
        pass


class Ok(HttpResponseAbstract):
    def __init__(self, data: Optional[Any]) -> None:
        if data is not None:
            self.data = data
        else:
            self.data = ""

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        return JSONResponse(content=self.data, status_code=200)


class Created(HttpResponseAbstract):
    def __init__(self, data: Optional[Any]) -> None:
        if data is not None:
            self.data = data
        else:
            self.data = ""

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        return JSONResponse(content=self.data, status_code=201)


class NoContent(HttpResponseAbstract):
    def __init__(self) -> None:
        pass

    def response(self) -> Response:
        """
        parse class to Response None
        """
        return Response(status_code=204)


class Unauthorized(HttpResponseAbstract):
    def __init__(
        self, message: str = "Unauthorized", custom_response: Optional[str] = None
    ) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Unauthorized'
        }
        status_code: 401
        """
        self.message = message
        self.custom_response = custom_response

    def response(self) -> JSONResponse:
        if self.custom_response is None:
            return JSONResponse(content={"message": f"{self.message}"}, status_code=401)
        return JSONResponse(content=self.custom_response, status_code=401)


class BadRequest(HttpResponseAbstract):
    def __init__(
        self, message: Optional[str] = None, custom_response: Optional[Any] = None
    ) -> None:
        """
        message: bad request message, for default json response
        custom_response: override default json response
        default json response:
        json:{
            'message': f'{message}'
        }
        status_code: 400

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=400)
        """
        self.custom_response = None
        if custom_response is None:
            self.message = message
        else:
            self.custom_response = custom_response

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response is None:
            return JSONResponse(content={"message": self.message}, status_code=400)
        else:
            return JSONResponse(content=self.custom_response, status_code=400)


class Forbidden(HttpResponseAbstract):
    def __init__(self, custom_response: Optional[Any] = None) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'You don\'t have permissions to perform this action'
        }
        status_code: 403

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=403)
        """
        self.custom_response = None
        if custom_response is None:
            self.message = "You don't have permissions to perform this action"
        else:
            self.custom_response = custom_response

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response is None:
            return JSONResponse(content={"message": self.message}, status_code=403)
        else:
            return JSONResponse(content=self.custom_response, status_code=403)


class NotFound(HttpResponseAbstract):
    def __init__(
        self, message: str = "Not Found", custom_response: Optional[Any] = None
    ) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Not Found'
        }
        status_code: 404
        """
        self.custom_response = None
        if custom_response is not None:
            self.custom_response = custom_response
        else:
            self.message = message

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response is None:
            return JSONResponse(content={"message": self.message}, status_code=404)
        else:
            return JSONResponse(content=self.custom_response, status_code=404)


class InternalServerError(HttpResponseAbstract):
    def __init__(
        self, error: Optional[str] = None, custom_response: Optional[Any] = None
    ) -> None:
        """
        error: error string for defaut json response
        custom_response: override default json response
        default json response:
        json:{
            'error': '{error}'
        }
        status_code: 500

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=500)
        """
        self.custom_response = None
        if custom_response is not None:
            self.custom_response = custom_response
        else:
            self.error = error

    def response(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response is None:
            raise HTTPException(status_code=500, detail="Something wrong with server")
        else:
            raise HTTPException(status_code=500, detail=self.custom_response)


def common_response(res: HttpResponseAbstract):
    return res.response()


def handle_http_exception(
    e: HTTPException,
) -> Union[None, JSONResponse, Response]:
    if e.status_code == 400:
        return common_response(BadRequest(message=e.detail))
    elif e.status_code == 401:
        return common_response(Unauthorized(message=e.detail))
    elif e.status_code == 403:
        return common_response(Forbidden(custom_response={"message": e.detail}))
    elif e.status_code == 404:
        return common_response(NotFound(message=e.detail))
    elif e.status_code == 422:
        return common_response(BadRequest(message=e.detail))
    elif e.status_code >= 500:
        return common_response(InternalServerError(error=e.detail))
    else:
        return common_response(
            InternalServerError(error=f"Unexpected error: {e.detail}")
        )
