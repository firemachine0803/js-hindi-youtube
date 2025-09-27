import requests
import time
import json
from datetime import datetime

# Telegram Bot Constants
BOT_TOKEN = "6732341545:AAErWzUWnrB16b9IRpC4FhBo7Aw7VT2h7kY"
CHAT_ID = "@akashbalance"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

class LotteryPredictor:
    def __init__(self):
        self.url = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
        self.current_prediction_issue = None
        self.predicted_issue = None
        self.prediction_type = None  # 'small' or 'big'
        
    def send_telegram_message(self, message):
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(TELEGRAM_URL, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False
    
    def get_lottery_data(self):
        """Fetch lottery data from the API"""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def analyze_number(self, number_str):
        """Analyze the number and return prediction type (small/big)"""
        try:
            number = int(number_str)
            
            # Numbers 0,1,2,3,4 predict Small
            if number in [0, 1, 2, 3, 4]:
                return "small"
            # Numbers 5,6,7,8,9 predict Big
            elif number in [5, 6, 7, 8, 9]:
                return "big"
            else:
                return "small"  # Default fallback
        except ValueError:
            print(f"Invalid number format: {number_str}")
            return "small"
    
    def get_issue_by_number(self, data, issue_number):
        """Find result by issue number in the list"""
        if data and 'data' in data and 'list' in data['data']:
            for item in data['data']['list']:
                if item['issueNumber'] == issue_number:
                    return item
        return None
    
    def increment_issue_number(self, issue_number, increment=2):
        """Increment the issue number by specified amount"""
        # Extract the numeric part and increment
        try:
            # Assuming format: YYYYMMDDHHMMSSXXX (last 3 digits are the sequence)
            base = issue_number[:-3]  # First part (date + time)
            sequence = int(issue_number[-3:])  # Last 3 digits (sequence)
            
            new_sequence = sequence + increment
            new_issue = f"{base}{new_sequence:03d}"  # Pad with leading zeros
            
            return new_issue
        except:
            # Fallback: try simple integer conversion if format changes
            try:
                return str(int(issue_number) + increment)
            except:
                return None
    
    def make_prediction(self, data):
        """Make prediction based on result.data.list[1]"""
        if not data or 'data' not in data or 'list' not in data['data']:
            return False
        
        if len(data['data']['list']) < 2:
            print("Not enough results in list")
            return False
        
        # Get the second item in the list (index 1)
        current_result = data['data']['list'][1]
        self.current_prediction_issue = current_result['issueNumber']
        current_number = current_result['number']
        
        print(f"📊 Base result: Issue {self.current_prediction_issue}, Number: {current_number}")
        
        # Analyze and make prediction
        self.prediction_type = self.analyze_number(current_number)
        
        # Calculate predicted issue number (current + 2)
        self.predicted_issue = self.increment_issue_number(self.current_prediction_issue, 2)
        
        if self.predicted_issue:
            # Send prediction to Telegram
            telegram_msg = f"Prediction for Issue : {self.predicted_issue},\nprediction: {self.prediction_type.upper()}"
            self.send_telegram_message(telegram_msg)
            
            print(f"🎯 Predicting for issue {self.predicted_issue}: {self.prediction_type.upper()}")
            print(f"📤 Sent to Telegram: {telegram_msg}")
        else:
            print("❌ Error calculating predicted issue number")
            
        return True
    
    def check_prediction(self, data):
        """Check prediction by finding the predicted issue in the list"""
        if not self.predicted_issue:
            print("❌ No prediction made yet")
            return None
        
        # Find the result for predicted issue
        predicted_result = self.get_issue_by_number(data, self.predicted_issue)
        
        if not predicted_result:
            print(f"❌ Result for predicted issue {self.predicted_issue} not found in current data")
            return "pending"  # Result not available yet
        
        actual_number = int(predicted_result['number'])
        
        # Determine if actual result is small or big
        if actual_number in [0, 1, 2, 3, 4]:
            actual_type = "small"
        else:  # Numbers 5,6,7,8,9 are big
            actual_type = "big"
        
        print(f"🆕 Actual result: Issue {self.predicted_issue}, Number: {actual_number} ({actual_type})")
        print(f"📋 Predicted: {self.prediction_type.upper()}")
        
        # Check if prediction matches
        if actual_type == self.prediction_type:
            result = "win"
        else:
            result = "loss"
        
        # Send result to Telegram
        if result == "win":
            telegram_msg = "WON ✅"
            self.send_telegram_message(telegram_msg)
            print("🎉 WIN! Prediction matched!")
        else:
            telegram_msg = "LOSS 🛑"
            self.send_telegram_message(telegram_msg)
            print("💥 LOSS! Prediction did not match.")
        
        return result
    
    def run(self):
        """Main loop to run the prediction system continuously"""
        print("🚀 Starting Lottery Prediction System...")
        print("=" * 60)
        
        # Send startup message to Telegram
        startup_msg = "🔮 Lottery Prediction Bot Started"
        self.send_telegram_message(startup_msg)
        
        prediction_made = False
        
        while True:
            try:
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking...")
                
                # Get current data
                data = self.get_lottery_data()
                if not data:
                    print("❌ Failed to get data, retrying in 30 seconds...")
                    time.sleep(3)
                    continue
                
                if not prediction_made:
                    # Step 1: Make prediction based on result.data.list[1]
                    print("🔮 Making prediction based on current data...")
                    if self.make_prediction(data):
                        prediction_made = True
                        print("⏳ Waiting for predicted result to be available...")
                    time.sleep(3)
                    
                else:
                    # Step 2: Check if predicted result is available
                    result = self.check_prediction(data)
                    
                    if result == "pending":
                        # Predicted result not available yet, keep waiting
                        print(f"⏳ Result for {self.predicted_issue} not available yet, checking again in 30 seconds...")
                        time.sleep(3)
                    else:
                        # Prediction resolved (win/loss)
                        print("=" * 60)
                        print("🔄 Starting new prediction cycle...")
                        prediction_made = False
                        time.sleep(5)  # Brief pause before next cycle
                
            except KeyboardInterrupt:
                print("\n🛑 Script stopped by user")
                # Send shutdown message to Telegram
                shutdown_msg = "🛑 Lottery Prediction Bot Stopped"
                self.send_telegram_message(shutdown_msg)
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(6)

def main():
    predictor = LotteryPredictor()
    predictor.run()

if __name__ == "__main__":
    main()