
import re
from backend.database import SessionLocal
from backend.models.job import Application
from backend.services.engine.template_constants import DYNAMIC_RESUME_HTML

db = SessionLocal()
apps = db.query(Application).all()

new_style_match = re.search(r'<style>(.*?)</style>', DYNAMIC_RESUME_HTML, re.DOTALL)
if new_style_match:
    new_style = new_style_match.group(1)
    count = 0
    for app in apps:
        if app.generated_html:
            app.generated_html = re.sub(r'<style>.*?</style>', f'<style>{new_style}</style>', app.generated_html, flags=re.DOTALL)
            count += 1
    db.commit()
    print(f'Successfully updated CSS in {count} applications.')
else:
    print('Failed to find new style in DYNAMIC_RESUME_HTML')
