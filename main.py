import cv2
import mediapipe as mp
import random
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

def get_hand_sign(hand_landmarks):
    finger_states = []
    tips_ids = [4, 8, 12, 16, 20]

    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        finger_states.append(1)
    else:
        finger_states.append(0)

    for tip in tips_ids[1:]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            finger_states.append(1)
        else:
            finger_states.append(0)

    if finger_states == [0, 0, 0, 0, 0]:
        return "rock"
    elif finger_states == [0, 1, 1, 0, 0]:
        return "scissors"
    elif finger_states == [1, 1, 1, 1, 1] or finger_states == [0, 1, 1, 1, 1]:
        return "paper"
    else:
        return None

def judge(player, computer):
    if player == computer:
        return "draw"
    elif (player == "rock" and computer == "scissors") or \
         (player == "scissors" and computer == "paper") or \
         (player == "paper" and computer == "rock"):
        return "player"
    else:
        return "computer"

def draw_text(img, text, pos, color=(255, 255, 255), size=2, thickness=4, outline_color=(0, 0, 0), outline_thickness=8):
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, size, outline_color, outline_thickness, lineType=cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, size, color, thickness, lineType=cv2.LINE_AA)

def draw_text_center(img, text, center, color=(255, 255, 255), size=2, thickness=4):
    (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, size, thickness)
    x = int(center[0] - text_width / 2)
    y = int(center[1] + text_height / 2)
    draw_text(img, text, (x, y), color, size, thickness)

player_score = 0
computer_score = 0
round_active = False
player_move = None
computer_move = None
show_result = False
result = ""
countdown = 3
countdown_start_time = 0
cooldown = 2
game_over = False

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    current_time = time.time()

    draw_text(img, f"Player: {player_score}  Computer: {computer_score}", (10, 50), (0, 255, 255), 1)

    if not round_active and not show_result and not game_over:
        # 新增：提示玩家出拳按 s 開始
        draw_text_center(img, "Press 's' to make your move", (img.shape[1] // 2, img.shape[0] // 2), (255, 255, 0), 1.2, 2)

    if round_active:
        elapsed = current_time - countdown_start_time
        if elapsed >= 1:
            countdown -= 1
            countdown_start_time = current_time

        if countdown > 0:
            draw_text_center(img, str(countdown), (img.shape[1] // 2, img.shape[0] // 3), (0, 255, 0), size=3, thickness=6)
        else:
            if results.multi_hand_landmarks:
                if len(results.multi_hand_landmarks) > 1:
                    draw_text(img, "Please use only ONE hand", (50, 400), (0, 0, 255), 1.2)
                    round_active = False
                else:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    player_move = get_hand_sign(hand_landmarks)
                    if player_move:
                        computer_move = random.choice(["rock", "paper", "scissors"])
                        result = judge(player_move, computer_move)

                        if result == "player":
                            player_score += 1
                        elif result == "computer":
                            computer_score += 1

                        show_result = True
                        round_active = False
                        countdown = 3

    elif show_result:
        draw_text(img, f"You: {player_move}", (50, 320), (255, 255, 0), 1.2)
        draw_text(img, f"Computer: {computer_move}", (50, 370), (255, 100, 100), 1.2)

        if result == "draw":
            draw_text_center(img, "Draw!", (img.shape[1] // 2, img.shape[0] // 2), (0, 255, 255), 2.5, 6)
        elif result == "player":
            draw_text_center(img, "You Win!", (img.shape[1] // 2, img.shape[0] // 2), (0, 255, 0), 2.5, 6)
        else:
            draw_text_center(img, "You Lose!", (img.shape[1] // 2, img.shape[0] // 2), (0, 0, 255), 2.5, 6)

        # 改動重點：結束顯示結果但不自動清除，讓玩家能隨時按 s 開啟下一回合
        # 玩家按 s 時會啟動新回合，不用等待 cooldown
        # 所以這裡不再用 cooldown 清除 show_result

    if player_score == 2 or computer_score == 2:
        winner_text = "You Win the Game!" if player_score == 2 else "Computer Wins the Game!"
        draw_text_center(img, winner_text, (img.shape[1] // 2, img.shape[0] // 4 - 20), (0, 255, 255), 1.2, 4)
        draw_text_center(img, "Press 'r' to restart or 'q' to quit.", (img.shape[1] // 2, img.shape[0] // 4 + 40), (255, 255, 255), 1.2, 4)
        game_over = True

    cv2.imshow("Rock Paper Scissors", img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('r'):
        player_score = 0
        computer_score = 0
        show_result = False
        round_active = False
        player_move = None
        computer_move = None
        countdown = 3
        game_over = False

    if key == ord('s'):
        # 新增：按 s 只要不是遊戲結束，都可直接開始新回合
        if not round_active and not game_over:
            round_active = True
            countdown = 3
            countdown_start_time = current_time
            show_result = False  # 開新回合前清除之前結果顯示

cap.release()
cv2.destroyAllWindows()
