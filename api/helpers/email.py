from dependencies.deps import FRONTEND_URL
from services.brevo_email import send_brevo_template_email
from services.token_service import create_token
from datetime import timedelta



async def send_confirmation_mail(email:str, user_id:int, user_role:str, first_name: str, last_name:str, company_name:str):

  token = create_token(email, user_id, user_role,expires_delta=timedelta(hours=24), token_type="email_confirm" )
  confirm_url = f"{FRONTEND_URL}/confirm-email?token={token}"

  await send_brevo_template_email(
      to_email=email,
      to_name=f"{first_name} {last_name}",
      template_id=1,
      params={
          "EMAIL": email,
          "COMPANY": company_name,
          "CONFIRM_URL": confirm_url,
      },
  )