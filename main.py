from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlmodel import select
from src.models.product_model import Product, ProductCategories
from src.shared.database.session_db import SessionDep, get_session

import boto3
import os

# 1. PRIMERO CREAMOS LA INSTANCIA DE FASTAPI
app = FastAPI()

# 2. INICIALIZAR EL CLIENTE DE AWS S3 (con la doble 's' en access)
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


# 3. ENDPOINTS DE SALUD Y S3
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "La aplicación está funcionando correctamente"}


@app.post("/images")
def upload_image(file: UploadFile = File(...)):
    # Validar que sea una imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo no permitido. Debe ser una imagen")

    try:
        # Subir el archivo al bucket S3 usando Boto3
        s3_client.upload_fileobj(file.file, BUCKET_NAME, file.filename)
        image_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file.filename}"

        return {"message": "Imagen subida exitosamente", "reference_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo a S3: {str(e)}")


# 4. MODELOS Y ENDPOINTS DEL CRUD DE PRODUCTOS
class CreateProduct(BaseModel):
    name: str
    price: float
    quantity: int
    category: ProductCategories


@app.post("/product", status_code=201)
def create_product(product: CreateProduct, session: SessionDep):
    # 1. Buscar si el producto existe
    product_inDb = session.exec(
        select(Product).where(Product.name == product.name.lower().strip())
    ).one_or_none()

    # 2.1 Si existe enviar mensaje de error
    if product_inDb == None:

        if product.price <= 0:
            raise HTTPException(
                status_code=422,
                detail="El precio del producto debe ser superior a 0",
            )

        if product.quantity <= 0:
            raise HTTPException(
                status_code=422,
                detail="La cantidad del producto debe ser superior a 0",
            )

        product = Product(
            name=product.name,
            category=product.category,
            price=product.price,
            quantity=product.quantity,
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        return product
    # 2.2 Si no existe continuar con la creacion
    else:
        raise HTTPException(
            status_code=409, detail="El producto ya existe en la base de datos"
        )


@app.get("/product")
def get_products(session: SessionDep):
    products = session.exec(select(Product)).all()
    return products


@app.delete("/product/{id}")
def delete_product(id: int, session: SessionDep):
    product = session.exec(select(Product).where(Product.id == id)).one()
    session.delete(product)
    session.commit()
    return {"message": "Producto eliminado exitosamente"}


@app.get("/product/{id}")
def get_product_by_id(id: int, session: SessionDep):
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@app.put("/product/{id}")
def update_product(id: int, product_data: CreateProduct, session: SessionDep):
    product_db = session.get(Product, id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if product_data.price <= 0:
        raise HTTPException(status_code=422, detail="El precio del producto debe ser superior a 0")
    if product_data.quantity <= 0:
        raise HTTPException(status_code=422, detail="La cantidad del producto debe ser superior a 0")

    product_db.name = product_data.name
    product_db.price = product_data.price
    product_db.quantity = product_data.quantity
    product_db.category = product_data.category

    session.add(product_db)
    session.commit()
    session.refresh(product_db)
    
    return product_db