from aiogram.fsm.state import State, StatesGroup


class AddMovieState(StatesGroup):
    waiting_for_video = State()  # Video yoki fayl yuborish
    waiting_for_title = State()  # Kino nomini kiritish
    waiting_for_code = State()   # Kino kodi (avtomatik yoki qo'lda)


class DeleteMovieState(StatesGroup):
    waiting_for_code = State()   # O'chiriladigan kino kodi


class BroadcastState(StatesGroup):
    waiting_for_message = State()      # 1. Avval xabar tashlanadi
    choosing_button_color = State()    # 2. Tugma rangi so'raladi (Qizil, Ko'k, Yashil, Klassik)
    waiting_for_button_text = State()  # 3. Tugma ustiga yoziladigan matn
    waiting_for_button_url = State()   # 4. Tugma uchun havola


class AddChannelState(StatesGroup):
    waiting_for_channel = State()      # Kanal ID yoki @username yoki post forwardi
    waiting_for_invite_link = State()  # Taklif havolasi


class AddSeriesState(StatesGroup):
    waiting_for_title = State()  # Serial nomi
    waiting_for_code = State()   # Serial kodi


class AddEpisodeState(StatesGroup):
    waiting_for_series_code = State()    # Serial kodi
    waiting_for_episode_number = State() # Qism raqami
    waiting_for_video = State()          # Qism videosi


class DeleteEpisodeState(StatesGroup):
    waiting_for_series_code = State()
    waiting_for_episode_number = State()


class DeleteSeriesState(StatesGroup):
    waiting_for_series_code = State()


