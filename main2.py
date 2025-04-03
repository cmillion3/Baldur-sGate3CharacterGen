import random
import threading
from ollama import chat
import customtkinter
import traits as bg  
from PIL import Image

customtkinter.set_default_color_theme("theme.json")

class BG3CharacterGenerator(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Baldur's Gate 3 Character Generator")
        self.geometry("850x625")
        self.configure(padx=10, pady=10)

        self.resizable(False, False)

        # Character Info
        self.entries = {}
        fields = ["Appearance", "Class", "Sub-Class", "Race", "Subrace", "Background", "Alignment", "Likes"]
        for i, field in enumerate(fields):
            label = customtkinter.CTkLabel(self, text=field + ":", anchor="w")
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            entry = customtkinter.CTkEntry(self, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[field] = entry

        # Load up a Character Image
        try:
            self.character_image = customtkinter.CTkImage(Image.open("default.png"), size=(350,350))
        except FileNotFoundError:
            print("Warning: default.png not found")
            self.character_image = None

        self.image_label = customtkinter.CTkLabel(self, image=self.character_image, text="")
        self.image_label.grid(row=0, column=2, rowspan=5, padx=10, pady=10)

        #Backstory Stuff
        self.backstory_label = customtkinter.CTkLabel(self, text="Backstory:")
        self.backstory_label.grid(row=5, column=2, padx=10, pady=5, sticky="w")

        self.backstory_textbox = customtkinter.CTkTextbox(self, width=250, height=100, wrap="word")
        self.backstory_textbox.grid(row=6, column=2, padx=10, pady=5)

        self.generate_backstory_button = customtkinter.CTkButton(self, text="Generate Backstory (ONLY USE WITH)", command=self.generate_backstory)
        self.generate_backstory_button.grid(row=7, column=2, columnspan=2, pady=10)

        #Generate Button
        self.generate_character_button = customtkinter.CTkButton(self, text="Generate Character", command=self.generate_character)
        self.generate_character_button.grid(row=8, column=0, columnspan=2, pady=10)

        #This is here so a character is generated on load
        self.generate_character()

    def generate_character(self): #This function does all the heavy lifting!
        appearance = random.choice(["Masculine", "Feminine"])
        char_class = random.choice(list(bg.classes.keys()))
        sub_class = random.choice(bg.classes[char_class])

        race = random.choice(list(bg.races.keys()))
        subrace = random.choice(bg.races[race]) if race not in ["Human", "Half-orc", "Githyanki"] else None

        background = random.choice(bg.backgrounds)

        alignment = random.choice(bg.alignment)
        if char_class == "Paladin":
            if random.choice([True, False]):  # Oathbreaker chance
                alignment = "Oathbreaker"
            else:
                while alignment.endswith("Evil") or alignment.endswith("Neutral"): # Since it doesn't make sense for a paladin to be anything but Good, you reroll if you don't get Oathbreaker until you're one of the goods
                    alignment = random.choice(bg.alignment)

        # Likes based on alignment
        if alignment.endswith("Good"):
            likes = ", ".join(random.choices(bg.likes["Good"], k=3))
        elif alignment.endswith("Evil"):
            likes = ", ".join(random.choices(bg.likes["Evil"], k=3))
        else:
            likes = ", ".join(random.choices(bg.likes["Evil"] + bg.likes["Good"], k=3))

        # Update text fields
        for field, value in [
            ("Appearance", appearance),
            ("Class", char_class),
            ("Sub-Class", sub_class),
            ("Race", race),
            ("Subrace", subrace if subrace else "None"),
            ("Background", background),
            ("Alignment", alignment),
            ("Likes", likes),
        ]:
            self.entries[field].delete(0, "end")
            self.entries[field].insert(0, value)
        
            # Update Image
        try:
            image_path = "masc.png" if appearance == "Masculine" else "fem.png"
            self.character_image = customtkinter.CTkImage(Image.open(image_path), size=(350, 350))
            self.image_label.configure(image=self.character_image)
        except FileNotFoundError:
            print("Couldn't fetch photo")

        # Clear backstory when generating a new character
        self.backstory_textbox.delete("1.0", "end")

    def generate_backstory(self):
        def run_backstory_generation():
            # Disable button to prevent multiple clicks
            self.generate_backstory_button.configure(state="disabled")

            appearance = self.entries["Appearance"].get()
            char_class = self.entries["Class"].get()
            sub_class = self.entries["Sub-Class"].get()
            race = self.entries["Race"].get()
            subrace = self.entries["Subrace"].get()
            background = self.entries["Background"].get()
            alignment = self.entries["Alignment"].get()

            backstory_prompt = (
                f"Create a Baldur's Gate 3 backstory for a {appearance} {race} "
                f"{subrace if subrace != 'None' else ''} {sub_class} {char_class} "
                f"of {alignment} alignment with a background of {background}."
            )

            try:
                stream = chat(
                    model='llama3.2',  
                    messages=[{'role': 'user', 'content': backstory_prompt}],
                    stream=True,
                )

                def update_textbox(new_text):
                    self.backstory_textbox.insert("end", new_text)
                    self.backstory_textbox.see("end")  # Auto-scroll

                self.backstory_textbox.delete("1.0", "end")  # Clear previous text

                for chunk in stream:
                    text_chunk = chunk['message']['content']
                    self.after(0, update_textbox, text_chunk)

            except Exception as e:
                print(f"Error generating backstory: {e}")

            finally:
                # Re-enable button when generation is done
                self.after(0, lambda: self.generate_backstory_button.configure(state="normal"))

        # Start generation in a separate thread
        threading.Thread(target=run_backstory_generation, daemon=True).start()


#Start the generator!
if __name__ == "__main__":
    app = BG3CharacterGenerator()
    app.mainloop()
