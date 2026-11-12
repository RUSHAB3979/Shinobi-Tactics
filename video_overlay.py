"""Optional silent intro playback driven by the normal game loop."""
from pathlib import Path
import pygame


class VideoOverlay:
    def __init__(self):
        self.capture=None
        self.frame=None
        self.elapsed=0
        self.index=-1

    @property
    def active(self):
        return self.capture is not None

    def start(self,path):
        self.close()
        if not Path(path).is_file():return False
        try:
            import cv2
        except ImportError:
            return False
        self.cv2=cv2
        capture=cv2.VideoCapture(str(path))
        if not capture.isOpened():
            capture.release()
            return False
        self.capture=capture
        self.fps=capture.get(cv2.CAP_PROP_FPS) or 30
        self.count=int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.elapsed=0
        self.index=-1
        self.frame=None
        return True

    def update(self,dt):
        if not self.active:return
        self.elapsed+=dt
        wanted=int(self.elapsed*self.fps)
        if self.count and wanted>=self.count:
            self.close()
            return
        if wanted==self.index:return
        if wanted-self.index>3:
            self.capture.set(self.cv2.CAP_PROP_POS_FRAMES,wanted)
            self.index=wanted-1
        while self.index<wanted:
            ok,frame=self.capture.read()
            self.index+=1
            if not ok:
                self.close()
                return
        rgb=self.cv2.cvtColor(frame,self.cv2.COLOR_BGR2RGB)
        self.frame=pygame.image.frombytes(rgb.tobytes(),(rgb.shape[1],rgb.shape[0]),"RGB")

    def draw(self,surface,font):
        if not self.active:return
        surface.fill((5,8,15))
        if self.frame:
            w,h=surface.get_size()
            scale=min(w/self.frame.get_width(),h/self.frame.get_height())
            image=pygame.transform.scale(self.frame,(round(self.frame.get_width()*scale),round(self.frame.get_height()*scale)))
            surface.blit(image,image.get_rect(center=(w//2,h//2)))
        surface.blit(font.render("ESC skip intro",True,(235,240,250)),(20,20))

    def close(self):
        if self.capture is not None:self.capture.release()
        self.capture=None
        self.frame=None
