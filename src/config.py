from pathlib import Path

project_folder = Path(__file__).parent.absolute()
cwd = Path.cwd()

APP_CONFIG = {
    'telegram_token': '',
    'CHAT_JID': '',
    'CHAT_PASS': '',
    'CHEFF_JID': '',
    'CHEFF_PASS': '',
    'IMAGE_JID': '',
    'IMAGE_PASS': '',
    'COMMON_DIR': project_folder / 'common',
    'UPLOADS_DIR': project_folder / 'uploads',
    'CNN_DIR': project_folder / 'cnn_model',
    'DIALOGFLOW': {
        'PROJECT_ID': '',
        'LANGUAGE_CODE': '',
        'SESSION_ID': '',
        'CREDENTIALS': str((project_folder / 'private_key.json').relative_to(cwd))
    },
}
