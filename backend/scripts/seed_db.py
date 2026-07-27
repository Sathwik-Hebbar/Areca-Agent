import os
import sys
from datetime import date, datetime, timedelta

# Ensure python path finds root packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.session import SessionLocal, engine
from backend.db.base import Base
import backend.db.models  # ensure models registered

from backend.db.models.core.user import User, UserRole
from backend.db.models.core.farmer_profile import FarmerProfile
from backend.db.models.core.farm import Farm, IrrigationType
from backend.db.models.core.crop_block import CropBlock, BlockStatus
from backend.db.models.agronomy.farm_activity import FarmActivity, ActivityType, LoggedVia
from backend.db.models.env.weather_reading import WeatherReading, WeatherSource
from backend.db.models.market.market_price import MarketPrice
from backend.auth.jwt_handler import hash_password


def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).filter(User.username == "farmer_demo").first():
            print("Database already contains seed data.")
            return

        print("Seeding sample data...")

        # 1. User & Farmer Profile
        user = User(
            username="farmer_demo",
            phone="9876543210",
            password_hash=hash_password("password123"),
            role=UserRole.FARMER
        )
        db.add(user)
        db.flush()

        profile = FarmerProfile(
            user_id=user.id,
            full_name="Ramesh Gowda",
            village="Thirthahalli",
            taluk="Thirthahalli",
            district="Shivamogga",
            state="Karnataka",
            pincode="577432",
            preferred_language="kn",
            preferred_mandi="Shivamogga APMC"
        )
        db.add(profile)
        db.flush()

        # 2. Farm
        farm = Farm(
            farmer_id=profile.id,
            farm_name="Green Plantation Plot #1",
            latitude=13.6961,
            longitude=75.2427,
            total_area_acres=4.5,
            soil_type="Red Laterite",
            irrigation_type=IrrigationType.DRIP
        )
        db.add(farm)
        db.flush()

        # 3. Crop Blocks (Perennial batches)
        block_a = CropBlock(
            farm_id=farm.id,
            block_name="Block A – 2018 Mature Planting",
            variety="Mangala",
            planting_date=date(2018, 6, 15),
            number_of_trees=450,
            spacing_meters=2.7,
            status=BlockStatus.ACTIVE,
            notes="High yield block, drip lines installed."
        )
        block_b = CropBlock(
            farm_id=farm.id,
            block_name="Block B – 2022 Young Batch",
            variety="Sumangala",
            planting_date=date(2022, 7, 10),
            number_of_trees=200,
            spacing_meters=2.7,
            status=BlockStatus.ACTIVE,
            notes="Young trees, vulnerable to yellow leaf disease."
        )
        db.add_all([block_a, block_b])
        db.flush()

        # 4. Activities (Fertilizer, Spraying, Harvest)
        act1 = FarmActivity(
            crop_block_id=block_a.id,
            activity_type=ActivityType.FERTILIZER,
            activity_date=date.today() - timedelta(days=20),
            product_used="NPK 15:15:15 + Neem Cake",
            quantity=150.0,
            quantity_unit="kg",
            cost=2800.0,
            performed_by="Self",
            details={"NPK": "15:15:15", "neem_cake_kg": 50},
            logged_via=LoggedVia.APP
        )
        act2 = FarmActivity(
            crop_block_id=block_a.id,
            activity_type=ActivityType.SPRAYING,
            activity_date=date.today() - timedelta(days=5),
            product_used="Bordeaux Mixture 1%",
            quantity=20.0,
            quantity_unit="litre",
            cost=850.0,
            performed_by="Hired Labor",
            details={"target_disease": "Koleroga Fruit Rot"},
            logged_via=LoggedVia.APP
        )
        act3 = FarmActivity(
            crop_block_id=block_b.id,
            activity_type=ActivityType.IRRIGATION,
            activity_date=date.today() - timedelta(days=1),
            quantity=2.0,
            quantity_unit="hours",
            logged_via=LoggedVia.AUTO
        )
        db.add_all([act1, act2, act3])

        # 5. Weather Readings
        weather = WeatherReading(
            farm_id=farm.id,
            temperature=27.5,
            humidity=85.0,
            rainfall_mm=12.4,
            source=WeatherSource.API
        )
        db.add(weather)

        # 6. Market Prices
        mandi_price = MarketPrice(
            mandi_name="Shivamogga APMC",
            commodity="arecanut_chali",
            price_per_kg=485.0,
            price_date=date.today(),
            source="data.gov.in"
        )
        db.add(mandi_price)

        db.commit()
        print("Successfully seeded sample data!")
        print(f"Sample User: username='farmer_demo', password='password123'")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
