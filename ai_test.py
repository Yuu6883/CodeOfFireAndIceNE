from ai.bot import AIBot
from core.gui import GUIEngine
from core.constants import LEAGUE
import tensorflow as tf

def main():
    
    sess = tf.InteractiveSession()

    engine = GUIEngine(league=LEAGUE.WOOD3, strict=False, debug=False, sleep=0)
    bot1 = engine.add_player(AIBot, sess)
    bot2 = engine.add_player(AIBot, sess)

    print(bot1)
    print(bot2)

    # bot1.training_agent.randomize()
    # bot2.training_agent.randomize()

    # bot1.moving_agent.randomize()
    # bot2.moving_agent.randomize()

    # engine.start()

    # Testing weight functions
    # print("Bot1 Prediction, Before:", bot1.training_agent.predict([0] * 14))
    # print("Bot2 Prediction, Before:", bot2.training_agent.predict([0] * 14))

    # bot1_weights = bot1.training_agent.get_weights()
    # bot2_weights = bot2.training_agent.get_weights()

    # bot1.training_agent.set_weights(bot2_weights)
    # bot2.training_agent.set_weights(bot1_weights)

    # print("Bot1 Prediction, After:", bot1.training_agent.predict([0] * 14))
    # print("Bot2 Prediction, After:", bot2.training_agent.predict([0] * 14))

    # print(bot.training_agent.h_out.eval())
    # copy = bot.training_agent.copy()
    # print(copy.predict([0] * 14))

if __name__ == "__main__":
    try:
        # import sys
        # sys.setrecursionlimit(10000)
        main()
    except KeyboardInterrupt:
        print("Exit")
    except Exception as e:
        print("Simulation crashed")
        print(e)