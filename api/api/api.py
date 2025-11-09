from ninja import NinjaAPI
from services.games.api import router as games_router
from services.users.api import router as user_router
from services.tracking.api import router as tracking_router
from services.boards.api import router as boards_router

from authentication.auth import TokenAuthentication
from authentication.api import auth_router
from authentication.api import registration_router
from services.users.api import extacc_router as external_accounts_router 


api = NinjaAPI(auth=TokenAuthentication(),
   title="Statlabs API",
   description="Statlabs API for retrieval of game and user information alongside authentication processing.")

api.add_router("/auth/", auth_router, tags=["Token Authentication"])
api.add_router("/auth/", registration_router, tags=["Registration"])

api.add_router("/users/accounts/", external_accounts_router, tags=["External accounts"])

api.add_router("/users/", user_router, tags=["User endpoints"])
api.add_router("/games/", games_router, tags=["Game information"])  
api.add_router("/track/", tracking_router, tags=["Stats & Achievements"])
api.add_router("/boards/", boards_router, tags=["Board endpoints"])




