from pydantic import BaseModel

class PlaceOrderRequest(BaseModel):
    open_url: str
    phone: str
    sms_code: str
    supplier_code: str = "drissionpage"
    order_id: str = ""
    product_code: str = ""
