


class AppData:
    def __init__(self):
        self.default_text_model = 'llama-3.2-90b-text-preview'
        self.default_vision_model = 'llama-3.2-11b-vision-preview'
        self.models = dict()
        self.known_vision_models = ['llama-3.2-11b-vision-preview', 'llava-v1.5-7b-4096-preview']
        self.history_size = 7
class UserData:
    def __init__(self):
        self.chosen_model=None
        self.user_history=[]
        self.system_prompt = {"role": "system", "content": "You are a helpful assistant."}
        self.user_history.append(self.system_prompt)
        self.previous_image=None
