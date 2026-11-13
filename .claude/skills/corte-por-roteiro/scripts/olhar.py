"""Olhar fora da câmera, quadro a quadro (pedido do autor, 07/11).

O autor grava lendo o monitor no computador: em vários takes ele desvia o olho por alguns
quadros e volta. Isso não pode ficar no corte, nem por milissegundos. Este script mede, em cada
quadro, a posição da íris dentro do olho e a rotação da cabeça (MediaPipe Face Mesh com íris) e
lista os trechos em que ele sai da câmera.

Rodar (o mediapipe não está no pyproject, entra só nesta execução):
    uv run --no-project --python 3.12 --with mediapipe==0.10.14 --with opencv-python-headless \
        python .claude/skills/corte-por-roteiro/scripts/olhar.py <video> [--de S] [--ate S] \
        [--saida olhar.json] [--escala 540]

Saída: JSON com a mediana de referência, os quadros medidos e os `eventos`
({ini, fim, quadros, tipo}) em segundos do vídeo de entrada. Inclinar a cabeça para cima é gesto,
não olhar (calibrado no cursos-gratis-ia), por isso não conta. Todo evento precisa ser
CONFERIDO NO QUADRO antes de cortar — o número aponta, o olho decide (regra 10).
"""
import argparse, json, statistics

import cv2
import mediapipe as mp
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--de", type=float, default=0.0)
ap.add_argument("--ate", type=float, default=None)
ap.add_argument("--saida", default="olhar.json")
ap.add_argument("--escala", type=int, default=540, help="largura usada na medição")
ap.add_argument("--limiar-iris", type=float, default=0.055)
ap.add_argument("--limiar-cabeca", type=float, default=0.09)
a = ap.parse_args()

cap = cv2.VideoCapture(a.video)
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
cap.set(cv2.CAP_PROP_POS_MSEC, a.de * 1000)
fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True, max_num_faces=1)


def razao(lm, iris, a_, b_, cima, baixo):
    ix = np.mean([lm[k].x for k in iris]); iy = np.mean([lm[k].y for k in iris])
    return (ix - lm[a_].x) / (lm[b_].x - lm[a_].x + 1e-9), (iy - lm[cima].y) / (lm[baixo].y - lm[cima].y + 1e-9)


quadros = []
n = int(round(a.de * fps))
while True:
    ok, f = cap.read()
    if not ok:
        break
    t = n / fps
    if a.ate is not None and t > a.ate:
        break
    h, w = f.shape[:2]
    if w > a.escala:
        f = cv2.resize(f, (a.escala, int(h * a.escala / w)))
    r = fm.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    q = {"t": round(t, 3)}
    if r.multi_face_landmarks:
        lm = r.multi_face_landmarks[0].landmark
        h1, _ = razao(lm, range(468, 473), 33, 133, 159, 145)
        h2, _ = razao(lm, range(473, 478), 362, 263, 386, 374)
        q["iris"] = round((h1 + h2) / 2, 4)
        q["cabeca"] = round((lm[1].x - lm[33].x) / (lm[263].x - lm[33].x + 1e-9), 4)
        q["aberto"] = round(((lm[145].y - lm[159].y) + (lm[374].y - lm[386].y)) / 2 / (lm[263].x - lm[33].x + 1e-9), 4)
    quadros.append(q)
    n += 1

medidos = [q for q in quadros if "iris" in q]
ref = {k: statistics.median(q[k] for q in medidos) for k in ("iris", "cabeca")} if medidos else {}

eventos, atual = [], None
for q in quadros:
    if "iris" not in q:
        tipo = "sem-rosto"
    else:
        tipo = None
        if q["aberto"] > 0.03 and abs(q["iris"] - ref["iris"]) > a.limiar_iris:
            tipo = "olho"
        if abs(q["cabeca"] - ref["cabeca"]) > a.limiar_cabeca:
            tipo = "cabeca" if tipo is None else "olho+cabeca"
    if tipo:
        if atual and q["t"] - atual["fim"] <= 2.5 / fps:
            atual["fim"] = q["t"]; atual["tipos"].add(tipo)
        else:
            atual = {"ini": q["t"], "fim": q["t"], "tipos": {tipo}}; eventos.append(atual)
for e in eventos:
    e["fim"] = round(e["fim"] + 1 / fps, 3)
    e["quadros"] = int(round((e["fim"] - e["ini"]) * fps))
    e["tipo"] = "+".join(sorted({p for t in e.pop("tipos") for p in t.split("+")}))

json.dump({"video": a.video, "fps": fps, "referencia": ref, "eventos": eventos, "quadros": quadros},
          open(a.saida, "w"), ensure_ascii=False)
for e in eventos:
    print(f"{e['ini']:8.2f}-{e['fim']:8.2f}s {e['quadros']:3d}q {e['tipo']}")
print(f"{len(eventos)} eventos · {len(quadros)} quadros · ref {ref}")
