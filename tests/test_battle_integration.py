import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import unittest
from unittest.mock import patch
import pygame
from client import Game
from server import GameServer
from video_overlay import VideoOverlay


class FakeNetwork:
    connected=True
    def __init__(self):self.sent=[]
    def send(self,message):self.sent.append(message)
    def close(self):self.connected=False


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.game=Game()
        self.game.player_id="P1"
        self.game.net=FakeNetwork()
        self.server=GameServer()
        self.server._broadcast=lambda message:None
        state=self.server.state
        state.phase="BATTLE"
        state.characters={"P1":"Itachi","P2":"Sasuke"}
        self.game._handle_server_msg({"type":"STATE",**state.snapshot()})

    def tearDown(self):
        self.server.sock.close()
        pygame.quit()

    def advance(self,seconds):
        for _ in range(round(seconds*60)):
            self.game._advance_presentation(1/60)

    def test_reflection_and_reflected_ko_use_actual_recipient(self):
        self.server.state.hp["P2"]=35
        self.server._process({"action":"JUTSU"},"P1")
        self.game._handle_server_msg({"type":"STATE",**self.server.state.snapshot()})
        self.advance(1.5)
        self.assertTrue(self.game.presentation.visible_shields["P1"])
        self.server._process({"action":"ULTIMATE"},"P2")
        snapshot={"type":"STATE",**self.server.state.snapshot()}
        self.assertTrue(snapshot["last_action"]["reflected"])
        self.assertEqual(snapshot["phase"],"GAME_OVER")
        self.game._handle_server_msg(snapshot)
        self.assertEqual(self.game.scene,"BATTLE")
        self.advance(1.1)
        self.assertEqual(self.game.presentation.visible_hp["P2"],10)
        self.advance(.1)
        self.assertEqual(self.game.effect.target,self.game._root("P2"))
        self.assertEqual(self.game.presentation.visible_hp["P2"],0)
        self.assertEqual(self.game.scene,"BATTLE")
        self.advance(2)
        self.assertEqual(self.game.scene,"GAME_OVER")
        self.assertEqual(self.game.player_anim.current_anim,"victory")
        self.assertEqual(self.game.enemy_anim.current_anim,"down")

    def test_rapid_clicks_send_one_action(self):
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.game.battle_buttons[0].rect.center)
        self.game._scene_battle([event,event],event.pos,1/60)
        self.assertEqual(self.game.net.sent,[{"action":"ATTACK"}])

    def test_long_frame_keeps_queued_actor_pose_in_sync(self):
        for pid in ("P1","P2"):
            self.server._process({"action":"ATTACK"},pid)
            self.game._handle_server_msg({"type":"STATE",**self.server.state.snapshot()})
        self.game._advance_presentation(1.1)
        self.assertEqual(self.game.presentation.active["last_action"]["by"],"P2")
        self.assertEqual(self.game.enemy_anim.current_anim,"attack")
        self.assertAlmostEqual(self.game.enemy_anim.elapsed,self.game.presentation.progress)

    def test_missing_camera_dependencies_results_in_miss(self):
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.game.battle_buttons[1].rect.center)
        with patch.dict("sys.modules",{"hand_sign_ui":None}):
            self.game._scene_battle([event],event.pos,1/60)
        self.assertEqual(self.game.net.sent,[{"action":"JUTSU","dmg":0}])

    def test_disconnect_clears_queue_and_releases_pending_command(self):
        self.server._process({"action":"ATTACK"},"P1")
        self.game._handle_server_msg({"type":"STATE",**self.server.state.snapshot()})
        self.advance(.1)
        self.game.submission_pending=True
        self.game._handle_server_msg({"type":"OPPONENT_DISCONNECTED"})
        self.assertFalse(self.game.presentation.busy)
        self.assertFalse(self.game.submission_pending)
        self.assertIsNone(self.game.player_anim)
        self.assertEqual(self.game.scene,"MENU")

    def test_rematch_resets_all_presentation_state(self):
        self.game.scene="GAME_OVER"
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.game.btn_play_again.rect.center)
        self.game._scene_game_over([event],event.pos,1/60)
        self.assertEqual(self.game.scene,"MENU")
        self.assertFalse(self.game.presentation.seen)
        self.assertIsNone(self.game.player_anim)
        self.assertIsNone(self.game.effect)

    def test_video_missing_file_falls_back_without_optional_import(self):
        video=VideoOverlay()
        self.assertFalse(video.start("not-present.mp4"))
        self.assertFalse(video.active)

    def test_existing_video_without_decoder_falls_back(self):
        from pathlib import Path
        path=Path(__file__).resolve().parents[1]/"assets/videos/Sasuke vs Itachi starting scene.mp4"
        self.assertTrue(path.is_file())
        with patch.dict("sys.modules",{"cv2":None}):
            self.assertFalse(VideoOverlay().start(path))

    def test_no_audio_device_is_supported(self):
        pygame.mixer.quit()
        self.game._play_sfx("Sasuke","attack")


if __name__=="__main__":unittest.main()
