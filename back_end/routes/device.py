

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List
import uuid
import os
import random
from motor.motor_asyncio import AsyncIOMotorClient


from  back_end.routes.auth import get_current_user  
from back_end.db.database import get_db

