"""One-off best-of long video (4 goals H2H) built and posted from the cloud: python -m fmm.bestof"""
import subprocess
from pathlib import Path
from fmm import longedit, thumb, youtube, poster
from fmm import inbox
fs={f['id']: f for f in inbox.videos(inbox.drive())}
M=str(inbox.download(fs['1BQ-oyjyMStrkbnbU_7IXzCPx9i7vjoyO'])); R=str(inbox.download(fs['19LWsOdAq0u4bVujNdQI5HBSjpfjPpPDu']))
Path('output/long').mkdir(parents=True, exist_ok=True)
out=Path('output/long/best_h2h.mp4')
longedit.make([(M,102,129),(M,215,242),(M,248,275),(M,304,331),(R,0,72),(R,88,154)],'4 GOALS!!',out,sub='H2H WIN • FC MOBILE')
subprocess.run(['ffmpeg','-v','error','-y','-ss','110','-i',M,'-frames:v','1','output/long/_f.png'])
thumb.cover_wide('output/long/_f.png','4 GOALS\nIN ONE GAME!!','output/long/best_h2h_cover.jpg',sub='FC MOBILE H2H')
nl='\n'
cap=(f"4 Goals in One Game! | FC Mobile H2H{nl}{nl}Watch every goal from this FC Mobile H2H win 🔥 Stay till the replays.{nl}"
     f"Real gameplay with the build-up and the finish, so you can copy the moves in your own matches.{nl}{nl}"
     f"🔔 Subscribe for daily FC Mobile cards, redeem codes and gameplay{nl}📘 Facebook: https://www.facebook.com/61577183936749{nl}"
     f"📸 Instagram: https://www.instagram.com/fc_fmm/{nl}{nl}FC Mobile gameplay, FC Mobile 26 H2H, EA Sports FC Mobile goals, FC Mobile tips{nl}{nl}"
     "#FCMobile #FCMobile26 #EASportsFCMobile #Gameplay #FMM")
yt='6jNVGlvne_U'  # already on YouTube (run 41181933709); this rerun posts Facebook only
fb=poster.fb_video(out, cap.replace('Subscribe','Follow'))
poster.fb_thumbnail(fb, Path('output/long/best_h2h_cover.jpg'))
poster.log({"kind":"long","file":str(out),"type":"long","youtube":yt,"facebook":fb})
print("POSTED youtube", yt, "facebook", fb)
