from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2AuthorizationCodeBearer

app=FastAPI()

oauth2_scheme = OAuth2AuthorizationCodeBearer(token_url = "token")  #here token_url is the API url where the id and pw is sent for verification and it responds with a token to us
                                                                    #OAuth2AuthorizationCodeBearer is used to authenticate the frontend with our API, it sends authorization with a bearer + token
@app.get("/items/")
async def read_items(token:Annotated[str,Depends(oauth2_scheme)]):
    return {"token":token}