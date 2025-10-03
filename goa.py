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
        self.url = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
        self.current_prediction_issue = None
        self.prediction_type = None
        self.last_checked_time = 0
        self.check_interval = 3  # Check every 30 seconds for new results
        self.send_predictions = False  # Flag to control sending predictions and results to Telegram
        self.last_processed_issue = None  # Track the last issue processed
        self.last_sent_issue = None  # Track the last issue sent to Telegram to avoid duplicates
        self.pending_predictions = {}  # Track pending predictions {issue: prediction_type}

    def send_telegram_message(self, message, issue_number):
        """Send message to Telegram, ensuring no duplicates for the same issue"""
        if issue_number == self.last_sent_issue:
            print(f"⛔ Skipped sending duplicate message for issue {issue_number}")
            return False
        try:
            payload = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(TELEGRAM_URL, data=payload, timeout=5)
            if response.status_code == 200:
                print(f"📤 Sent to Telegram: {message} for issue {issue_number}")
                self.last_sent_issue = issue_number  # Update last sent issue
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    def get_lottery_data(self):
        """Fetch lottery data from the API"""
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data or 'data' not in data or 'list' not in data['data'] or len(data['data']['list']) < 2:
                print("❌ Invalid or insufficient API data")
                return None
            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return None

    def analyze_number(self, number_str):
        """Analyze the number and return prediction type (small/big)"""
        try:
            number = int(number_str)
            return "small" if number in [0, 1, 2, 3, 4] else "big"
        except ValueError:
            print(f"❌ Invalid number format: {number_str}")
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
        try:
            base = issue_number[:-3]
            sequence = int(issue_number[-3:])
            new_sequence = sequence + increment
            return f"{base}{new_sequence:03d}"
        except Exception as e:
            print(f"❌ Error incrementing issue number: {e}")
            try:
                return str(int(issue_number) + increment)
            except:
                return None

    def make_prediction(self, data):
        """Make prediction based on result.data.list[1]"""
        current_result = data['data']['list'][1]
        current_issue = current_result['issueNumber']
        
        # Skip if this issue was already processed
        if current_issue == self.last_processed_issue:
            print(f"⛔ Already processed issue {current_issue}, skipping")
            return False

        self.current_prediction_issue = current_issue
        current_number = current_result['number']
        print(f"📊 Base result: Issue {self.current_prediction_issue}, Number: {current_number}")

        predicted_issue = self.increment_issue_number(self.current_prediction_issue, 2)
        if not predicted_issue:
            print("❌ Failed to generate predicted issue number")
            return False

        self.prediction_type = self.analyze_number(current_number)
        self.pending_predictions[predicted_issue] = self.prediction_type  # Track pending prediction
        self.last_processed_issue = self.current_prediction_issue  # Update last processed issue

        if self.send_predictions:
            telegram_msg = f"✅ GOA 30sec : {predicted_issue},\nprediction: {self.prediction_type.upper()}"
            if self.send_telegram_message(telegram_msg, predicted_issue):
                print(f"🎯 Predicting for issue {predicted_issue}: {self.prediction_type.upper()}")
                return True
            else:
                print("❌ Failed to send prediction to Telegram")
                return False
        else:
            print(f"🎯 Prediction for issue {predicted_issue}: {self.prediction_type.upper()} (not sent, waiting for win)")
            telegram_msg = f"❌ Skipp {predicted_issue}"
            if self.send_telegram_message(telegram_msg, predicted_issue):
                return True
            else:
                print("❌ Failed to send Skipp message to Telegram")
                return False

    def check_prediction(self, data):
        """Check all pending predictions"""
        resolved_issues = []
        for issue, prediction_type in list(self.pending_predictions.items()):
            predicted_result = self.get_issue_by_number(data, issue)
            if not predicted_result:
                print(f"⏳ Result for {issue} not available yet")
                continue

            actual_number = int(predicted_result['number'])
            actual_type = "small" if actual_number in [0, 1, 2, 3, 4] else "big"

            print(f"🆕 Actual result: Issue {issue}, Number: {actual_number} ({actual_type})")
            print(f"📋 Predicted: {prediction_type.upper()}")

            result = "win" if actual_type == prediction_type else "loss"
            
            # Store current state to check if we need to send win/loss messages
            was_sending_predictions = self.send_predictions
            
            # Update send_predictions flag
            if result == "win":
                self.send_predictions = True  # Switch on: enable sending predictions
            else:
                self.send_predictions = False  # Switch off: stop sending predictions
            
            # Send messages only if predictions were already being sent
            if was_sending_predictions:
                if result == "win":
                    telegram_msg = (
                        "WON ✅✅✅✅✅✅ \n<a href=\"https://www.goagames.bio/#/register?invitationCode=484226564353\">👉🏼CLICK HERE TO REGISTER👈🏼</a>\n<a href=\"https://www.goagames.bio/#/register?invitationCode=484226564353\">👉🏼यहाँ क्लिक करें👈🏼</a>"
                    )
                    self.send_telegram_message(telegram_msg, issue)
                    print("🎉 WIN! Prediction matched!")
                else:
                    telegram_msg = "LOSS 🛑🛑🛑🛑🛑🛑"
                    self.send_telegram_message(telegram_msg, issue)
                    print("💥 LOSS! Prediction did not match.")
            else:
                print(f"{'🎉 WIN!' if result == 'win' else '💥 LOSS!'} Prediction {'matched' if result == 'win' else 'did not match'} (not sent, {'enabling predictions' if result == 'win' else 'waiting for win'})")

            resolved_issues.append(issue)  # Mark issue as resolved

        # Remove resolved predictions
        for issue in resolved_issues:
            del self.pending_predictions[issue]

        return bool(resolved_issues)  # Return True if any predictions were resolved

    def run(self):
        """Main loop to run the prediction system continuously"""
        print("🚀 Starting Lottery Prediction System...")
        print("=" * 60)
        self.send_telegram_message("🔮 Lottery Prediction Bot Started", "startup")

        last_issue_seen = None

        while True:
            try:
                current_time = time.time()
                # Only check data if interval has passed and there are pending predictions
                if current_time - self.last_checked_time < self.check_interval and self.pending_predictions:
                    time.sleep(1)
                    continue

                self.last_checked_time = current_time
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking...")

                data = self.get_lottery_data()
                if not data:
                    print("❌ Failed to get data, retrying...")
                    time.sleep(5)
                    continue

                latest_issue = data['data']['list'][0]['issueNumber'] if data and 'data' in data and 'list' in data['data'] else None
                if latest_issue == last_issue_seen and self.pending_predictions:
                    print("⏳ No new data available, waiting for pending results")
                    time.sleep(1)
                    continue
                last_issue_seen = latest_issue

                # Check all pending predictions
                self.check_prediction(data)

                # Make new prediction only if all pending predictions are resolved
                if not self.pending_predictions:
                    if self.make_prediction(data):
                        print(f"📝 New prediction made for issue {self.predicted_issue}")
                    else:
                        print("❌ Failed to make new prediction")
                        time.sleep(5)  # Brief pause to avoid spamming API
                else:
                    print(f"⏳ Waiting for {len(self.pending_predictions)} pending predictions: {list(self.pending_predictions.keys())}")

            except KeyboardInterrupt:
                print("\n🛑 Script stopped by user")
                self.send_telegram_message("🛑 Lottery Prediction Bot Stopped", "shutdown")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

def main():
    predictor = LotteryPredictor()
    predictor.run()

if __name__ == "__main__":
    main()