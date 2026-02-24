"""
Post-process and draw object detection results (with optional ByteTrack tracking).
Expects raw Hailo YOLO-style output: list of per-class arrays, each det = [bbox, score].
"""
import cv2
import numpy as np
import os
from collections import deque

from .toolbox import id_to_color
from .tracker import BYTETracker

tracklet_history = {}
trail_length = 30
TRACKLET_CLASSES = [0, 67]  # PERSON, SMARTPHONE (COCO)


def inference_result_handler(
    original_frame, infer_results, labels, config_data, tracker=None, draw_trail=False
):
    detections = extract_detections(original_frame, infer_results, config_data)
    frame_with_detections = draw_detections(
        detections, original_frame, labels, tracker=tracker, draw_trail=draw_trail
    )
    return frame_with_detections


def draw_detection(
    image, box, labels, score, color, track=False
):
    xmin, ymin, xmax, ymax = map(int, box)
    cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    if not track or len(labels) == 1:
        top_text = f"{labels[0]}: {score:.1f}%"
    else:
        top_text = f"{score:.1f}%"
    bottom_text = labels[1] if track and len(labels) == 2 else (labels[0] if track else None)
    text_color = (255, 255, 255)
    border_color = (0, 0, 0)
    cv2.putText(
        image, top_text, (xmin + 4, ymin + 20), font, 0.5, border_color, 2, cv2.LINE_AA
    )
    cv2.putText(
        image, top_text, (xmin + 4, ymin + 20), font, 0.5, text_color, 1, cv2.LINE_AA
    )
    if bottom_text:
        pos = (xmax - 50, ymax - 6)
        cv2.putText(
            image, bottom_text, pos, font, 0.5, border_color, 2, cv2.LINE_AA
        )
        cv2.putText(
            image, bottom_text, pos, font, 0.5, text_color, 1, cv2.LINE_AA
        )


def denormalize_and_rm_pad(
    box, size, padding_length, input_height, input_width
):
    box = [int(x * size) for x in box]
    for i in range(4):
        if i % 2 == 0:
            if input_height != size:
                box[i] -= padding_length
        else:
            if input_width != size:
                box[i] -= padding_length
    return [box[1], box[0], box[3], box[2]]


def extract_detections(image, detections, config_data):
    visualization_params = config_data.get("visualization_params", {})
    score_threshold = visualization_params.get("score_thres", 0.5)
    max_boxes = visualization_params.get("max_boxes_to_draw", 50)

    img_height, img_width = image.shape[:2]
    size = max(img_height, img_width)
    padding_length = int(abs(img_height - img_width) / 2)

    all_detections = []
    for class_id, detection in enumerate(detections):
        for det in detection:
            bbox, score = det[:4], det[4]
            if score >= score_threshold:
                denorm_bbox = denormalize_and_rm_pad(
                    bbox, size, padding_length, img_height, img_width
                )
                all_detections.append((score, class_id, denorm_bbox))

    all_detections.sort(reverse=True, key=lambda x: x[0])
    top_detections = all_detections[:max_boxes]
    if top_detections:
        scores, class_ids, boxes = zip(*top_detections)
    else:
        scores, class_ids, boxes = [], [], []

    return {
        "detection_boxes": list(boxes),
        "detection_classes": list(class_ids),
        "detection_scores": list(scores),
        "num_detections": len(top_detections),
    }


def draw_detections(
    detections, img_out, labels, tracker=None, draw_trail=False
):
    boxes = detections["detection_boxes"]
    scores = detections["detection_scores"]
    num_detections = detections["num_detections"]
    classes = detections["detection_classes"]

    if tracker:
        dets_for_tracker = [[*boxes[i], scores[i]] for i in range(num_detections)]
        if not dets_for_tracker:
            return img_out
        online_targets = tracker.update(np.array(dets_for_tracker))

        for track in online_targets:
            track_id = track.track_id
            x1, y1, x2, y2 = track.tlbr
            xmin, ymin, xmax, ymax = int(x1), int(y1), int(x2), int(y2)
            best_idx = find_best_matching_detection_index(track.tlbr, boxes)
            color = tuple(id_to_color(classes[best_idx] if best_idx is not None else 0).tolist())
            if best_idx is None:
                draw_detection(
                    img_out,
                    [xmin, ymin, xmax, ymax],
                    [f"ID {track_id}"],
                    track.score * 100.0,
                    color,
                    track=True,
                )
            else:
                draw_detection(
                    img_out,
                    [xmin, ymin, xmax, ymax],
                    [labels[classes[best_idx]], f"ID {track_id}"],
                    track.score * 100.0,
                    color,
                    track=True,
                )

            if best_idx is None or classes[best_idx] not in TRACKLET_CLASSES:
                continue
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            centroid = (center_x, center_y)
            if track_id not in tracklet_history:
                tracklet_history[track_id] = deque(maxlen=trail_length)
            tracklet_history[track_id].append(centroid)
            if draw_trail:
                for i in range(1, len(tracklet_history[track_id])):
                    point_a = tracklet_history[track_id][i - 1]
                    point_b = tracklet_history[track_id][i]
                    cv2.line(img_out, point_a, point_b, color, 3)
                    cv2.circle(img_out, point_b, radius=20, thickness=1, color=color)
    else:
        for idx in range(num_detections):
            color = tuple(id_to_color(classes[idx]).tolist())
            draw_detection(
                img_out, boxes[idx], [labels[classes[idx]]], scores[idx] * 100.0, color
            )
    return img_out


def find_best_matching_detection_index(track_box, detection_boxes):
    best_iou = 0
    best_idx = -1
    for i, det_box in enumerate(detection_boxes):
        iou = compute_iou(track_box, det_box)
        if iou > best_iou:
            best_iou = iou
            best_idx = i
    return best_idx if best_idx != -1 else None


def compute_iou(boxA, boxB):
    xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
    xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    areaB = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
    return inter / (areaA + areaB - inter + 1e-5)
