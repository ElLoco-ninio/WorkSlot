from sqlmodel import Session, select
from app.database import engine
from app.models import Profile

def check_slugs():
    with Session(engine) as session:
        profiles = session.exec(select(Profile)).all()
        print(f"Found {len(profiles)} profiles.")
        for p in profiles:
            print(f"ID: {p.id}, Business: {p.business_name}, Slug: {p.slug}")
            
            if not p.slug:
                print("  -> Slug is missing! Generating...")
                base_slug = p.business_name.lower().replace(" ", "-")
                p.slug = f"{base_slug}-{p.user_id}"
                session.add(p)
                print(f"  -> New Slug: {p.slug}")
        
        session.commit()
        print("Done.")

if __name__ == "__main__":
    check_slugs()
