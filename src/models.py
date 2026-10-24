from pydantic import BaseModel


class HelpdeskResponse(BaseModel):
    response:str
    chat_id:int
    user_id:int

