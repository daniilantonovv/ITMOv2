from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

CART_HOST = "vkusvill.ru"


def vkusvill_https_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (host == CART_HOST or host.endswith("." + CART_HOST)):
        raise ValueError(f"cart_url must be an https link on {CART_HOST}")
    return url


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Category = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
CartUrl = Annotated[str, AfterValidator(vkusvill_https_url)]
NonNegative = Annotated[float, Field(ge=0)]


class Product(BaseModel):
    name: ProductName
    price: NonNegative
    quantity: Annotated[int, Field(ge=1)] = 1
    kcal: NonNegative = 0
    protein: NonNegative = 0
    fat: NonNegative = 0
    carbs: NonNegative = 0


class CollectionIn(BaseModel):
    title: Title
    category: Category
    cart_url: CartUrl
    products: Annotated[list[Product], Field(min_length=1, max_length=100)]


class Totals(BaseModel):
    price: float
    kcal: float
    protein: float
    fat: float
    carbs: float

    @classmethod
    def of(cls, products: list[Product]) -> "Totals":
        def total(field: str) -> float:
            return round(sum(getattr(p, field) * p.quantity for p in products), 2)

        return cls(**{field: total(field) for field in cls.model_fields})


class CollectionSummary(BaseModel):
    id: int
    title: str
    category: str
    cart_url: str
    created_at: str
    product_count: int
    totals: Totals


class Collection(BaseModel):
    id: int
    title: str
    category: str
    cart_url: str
    created_at: str
    products: list[Product]
    totals: Totals

    def summary(self) -> CollectionSummary:
        return CollectionSummary(
            **self.model_dump(exclude={"products"}), product_count=len(self.products)
        )


class CategoryCount(BaseModel):
    category: str
    count: int
