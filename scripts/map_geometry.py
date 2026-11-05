from collections import defaultdict
import numpy as np

def contours(mask):
 h,w=mask.shape;edges=defaultdict(list)
 for y,x in zip(*np.where(mask)):
  if y==0 or not mask[y-1,x]:edges[(x,y)].append((x+1,y))
  if x==w-1 or not mask[y,x+1]:edges[(x+1,y)].append((x+1,y+1))
  if y==h-1 or not mask[y+1,x]:edges[(x+1,y+1)].append((x,y+1))
  if x==0 or not mask[y,x-1]:edges[(x,y+1)].append((x,y))
 while edges:
  start=next(iter(edges));p=start;poly=[p]
  while True:
   q=edges[p].pop()
   if not edges[p]:del edges[p]
   poly.append(q);p=q
   if p==start:break
  yield poly
def simplify(points,eps=1.15):
 if len(points)<3:return points
 a,b=np.array(points[0],float),np.array(points[-1],float);p=np.array(points,float);v=b-a
 if np.dot(v,v)==0:dist=np.linalg.norm(p-a,axis=1)
 else:
  t=np.clip((p-a)@v/np.dot(v,v),0,1);dist=np.linalg.norm(p-(a+t[:,None]*v),axis=1)
 j=int(np.argmax(dist))
 if dist[j]<=eps:return [points[0],points[-1]]
 return simplify(points[:j+1],eps)[:-1]+simplify(points[j:],eps)
def area(poly):return sum(x0*y1-x1*y0 for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]))/2
