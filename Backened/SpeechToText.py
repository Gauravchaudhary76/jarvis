from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os 
import time
import threading
import subprocess
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")  # Default to English

class JarvisSpeechRecognition:
    def __init__(self):
        self.driver = None
        self.server_process = None
        
    def create_html_file(self):
        """Create the HTML file for speech recognition"""
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <div id="status">Ready</div>
    <script>
        const output = document.getElementById('output');
        const status = document.getElementById('status');
        let recognition;
        let isRecognizing = false;

        function startRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                output.textContent = "Speech recognition not supported in this browser.";
                return;
            }
            
            recognition = new SpeechRecognition();
            recognition.lang = 'LANGUAGE_PLACEHOLDER';
            recognition.continuous = false;  // Changed to false for better control
            recognition.interimResults = false;

            recognition.onstart = function() {
                status.textContent = "Listening...";
                isRecognizing = true;
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                output.textContent = transcript;
                status.textContent = "Speech captured";
            };

            recognition.onend = function() {
                status.textContent = "Recognition ended";
                isRecognizing = false;
            };

            recognition.onerror = function(event) {
                status.textContent = "Error: " + event.error;
                isRecognizing = false;
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition && isRecognizing) {
                recognition.stop();
            }
        }

        function clearOutput() {
            output.textContent = "";
            status.textContent = "Ready";
        }
    </script>
</body>
</html>'''
        
        # Replace language placeholder
        html_code = html_code.replace("'LANGUAGE_PLACEHOLDER'", f"'{InputLanguage}'")
        
        # Create Data directory if it doesn't exist
        os.makedirs("Data", exist_ok=True)
        
        with open("Data/Voice.html", "w", encoding='utf-8') as f:
            f.write(html_code)
    
    def start_server(self):
        """Start HTTP server in a separate thread"""
        def run_server():
            try:
                os.chdir('Data')
                self.server_process = subprocess.Popen(['python', '-m', 'http.server', '8000'])
                os.chdir('..')  # Go back to original directory
            except Exception as e:
                print(f"Error starting server: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Give server time to start
    
    def setup_driver(self):
        """Setup Chrome driver with proper options"""
        chrome_options = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-file-access-from-files")
        chrome_options.add_argument("--use-file-for-fake-audio-capture=Data/audio.wav")  # Optional: for testing
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return False
        return True
    
    def set_assistant_status(self, status):
        """Set assistant status"""
        temp_dir_path = "Frontend/Files"  # Fixed typo
        os.makedirs(temp_dir_path, exist_ok=True)
        
        try:
            with open(f'{temp_dir_path}/Status.data', "w", encoding='utf-8') as file:
                file.write(status)
        except Exception as e:
            print(f"Error setting status: {e}")
    
    def query_modifier(self, query):
        """Modify the query by adding proper punctuation"""
        if not query:
            return ""
            
        new_query = query.lower().strip()
        query_words = new_query.split()
        
        if not query_words:
            return ""
        
        question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
        
        # Check if it's a question
        is_question = any(new_query.startswith(word) for word in question_words)
        
        # Remove existing punctuation
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1]
        
        # Add appropriate punctuation
        if is_question:
            new_query += "?"
        else:
            new_query += "."
        
        return new_query.capitalize()
    
    def universal_translate(self, text):
        """Translate text to English"""
        try:
            english_translation = mt.translate(text, "en", "auto")
            return english_translation.capitalize()
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def speech_recognition(self, timeout=30):
        """Perform speech recognition"""
        link = "http://localhost:8000/Voice.html"
        
        try:
            self.driver.get(link)
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for page to load and click start button
            start_button = wait.until(EC.element_to_be_clickable((By.ID, "start")))
            start_button.click()
            
            print("Listening... Speak now!")
            
            # Wait for speech input with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    output_element = self.driver.find_element(By.ID, "output")
                    text = output_element.text.strip()
                    
                    if text:
                        # Stop recognition
                        try:
                            end_button = self.driver.find_element(By.ID, "end")
                            end_button.click()
                        except:
                            pass
                        
                        print(f"Raw speech: {text}")
                        
                        # Process the text
                        if InputLanguage.lower().startswith("en"):
                            return self.query_modifier(text)
                        else:
                            self.set_assistant_status("Translating")
                            translated_text = self.universal_translate(text)
                            return self.query_modifier(translated_text)
                
                except Exception as e:
                    pass
                
                time.sleep(0.5)
            
            print("No speech detected within timeout period")
            return None
            
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.server_process:
            self.server_process.terminate()
    
    def run(self):
        """Main execution method"""
        try:
            # Setup
            self.create_html_file()
            self.start_server()
            
            if not self.setup_driver():
                print("Failed to setup driver")
                return
            
            print("Jarvis Speech Recognition Started")
            print("Press Ctrl+C to stop")
            
            while True:
                self.set_assistant_status("Listening")
                text = self.speech_recognition()
                
                if text:
                    print(f"Recognized: {text}")
                    self.set_assistant_status("Processing")
                    # Here you can add your voice command processing logic
                    # process_voice_command(text)
                else:
                    print("No speech recognized, trying again...")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping Jarvis...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    # Create .env file example if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("InputLanguage=en-US\n")
        print("Created .env file with default language settings")
    
    jarvis = JarvisSpeechRecognition()
    jarvis.run()


