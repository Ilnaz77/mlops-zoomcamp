from prefect_email import EmailServerCredentials

credentials = EmailServerCredentials(
    username="sali****",
    password="******",  # must be an app password

)
credentials.save("mail", overwrite=True)