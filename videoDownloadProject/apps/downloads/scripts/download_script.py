from django.contrib.auth import get_user_model

# video_url = "https://www.youtube.com/shorts/k_B1gm9sMiA" # 7MB
# video_url = "https://www.youtube.com/shorts/CRwjDoEWa2k?feature=share" # 35MB
# video_url = "https://www.youtube.com/shorts/hE_jWgregjM?feature=share"
# video_url = "https://www.youtube.com/shorts/c0l72MYI6GA"
# video_url = "https://www.youtube.com/shorts/RTqJMjoSFUI?feature=share"
# video_url = "https://www.youtube.com/shorts/9FZVIM-1Lkw?feature=share"
# video_url = "https://www.youtube.com/watch?v=if99Olw78WE&list=PLeXyx0kOyiXu_ju_10w9qDzqSDXYpqXD" #
# video_url = "https://www.youtube.com/watch?v=YeCn3or0XWs&list=PLbpi6ZahtOH7MBdd2q811v_7Tu31vnsyq"
# video_url = "https://www.youtube.com/watch?v=JKQow_FjMgg&list=PLEgVzQyXPPoM6NuiSX0vPeKtWl-aqMfEY" # playlist
# video_url = "https://www.youtube.com/watch?v=zpLkQVW8lmw&pp=ygUYZGphbmdvIHRpcHMgcHJvZmVzc2lvbmFs"
# video_url = "https://www.youtube.com/watch?v=cukQ7e9FEik&pp=ygUYZGphbmdvIHRpcHMgcHJvZmVzc2lvbmFs"  # 35MB


def run():
    user_model = get_user_model()
    # user = user_model.objects.first()
    user = user_model.objects.filter(username="shell-t-user").first()
    # if user is None:
    #     user = user_model.objects.get_or_create(
    #         username="anonymous-user", password="anonymous-pass"
    #     )
    print(user)
