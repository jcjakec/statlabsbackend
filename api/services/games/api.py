from utils.schemas import ErrorOut
from ninja import Router
from ninja.pagination import paginate, PageNumberPagination
from .models import Game, Platform, Company, Tag, GameInstance
from .schemas import GameSchema, TagSchema, CompanySchema, PlatformSchema
from django.db.models import Q

router = Router()

# Game endpoints
@router.get("", response=list[GameSchema])
@paginate(PageNumberPagination, page_size=20)
def all_games_with_search(request,     
    search: str = None,
    order: str = None,
    lth: bool = False,
    tags: str = None, 
    companies: str = None):

    query = Game.objects.prefetch_related("tags", "companies", "game_instances").all()

    if search:
        query = query.filter(Q(name__icontains=search) | Q(aliases__icontains=search))

    if tags:
        tags = [tag.strip() for tag in tags.split(',')]
        query = query.filter(Q(tags__slug__in=tags) | Q(tags__name__in=tags))

    if companies:
        companies = [company.strip() for company in companies.split(',')]
        query = query.filter(Q(companies__slug__in=companies) | Q(companies__name__in=companies))

    order_prefix = "" if lth else "-"
    if order == "popularity":
        query = query.order_by(f"{order_prefix}popularity")
    elif order == "name": 
        query = query.order_by(f"{order_prefix}name")
    else:
        query = query.order_by(f"{order_prefix}popularity")

    return query

# Inidividual game endpoint
@router.get("/{game_id}", response={200: GameSchema, 404: ErrorOut})
def game_by_id(request, game_id: int):
    try:
        game = Game.objects.prefetch_related("tags", "companies", "game_instances").get(id=game_id)
        return game
    except Game.DoesNotExist:
        return 404, {"message": "Game not found"}


# Other endpoints for specifc data if needed
@router.get("/tags", response=list[TagSchema])
@paginate(PageNumberPagination)
def all_tags(request):
    return Tag.objects.all().order_by("name")

@router.get("/tags/{tag_id}", response={200: TagSchema, 404: ErrorOut})
def tag_by_id(request, tag_id: int):
    try:
        tag = Tag.objects.get(id=tag_id)
        return tag
    except Tag.DoesNotExist:
        return 404, {"message": "Tag not found"}

@router.get("/platforms", response=list[PlatformSchema])
@paginate(PageNumberPagination)
def all_platforms(request): 
    return Platform.objects.all()

@router.get("/platforms/{platform_id}", response={200: PlatformSchema, 404: ErrorOut})
def platform_by_id(request, platform_id: int):
    try:
        platform = Platform.objects.get(id=platform_id)
        return platform
    except Platform.DoesNotExist:
        return 404, {"message": "Platform not found"}

@router.get("/companies", response=list[CompanySchema])
@paginate(PageNumberPagination)
def all_companies(request):
    return Company.objects.all()

@router.get("/companies/{company_id}", response={200: CompanySchema, 404: ErrorOut})
def company_by_id(request, company_id: int):
    try:
        company = Company.objects.get(id=company_id)
        return company
    except Company.DoesNotExist:
        return 404, {"message": "Company not found"}