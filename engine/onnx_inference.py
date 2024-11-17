import onnxruntime as ort
import cv2
import numpy as np
import dxcam


# Load ONNX Model
def load_model(model_path, provider):

    session = ort.InferenceSession(model_path, providers=[provider])
    input_details = session.get_inputs()[0]

    print("Execution providers:", session.get_providers())
    return session, input_details


# Preprocess Input Image
def preprocess_image(input_size, image_path=None, image=None):
    if image_path is not None:

        img = cv2.imread(image_path)
    else:
        img = image
    original_shape = img.shape[:2]
    img = cv2.resize(img, input_size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0  # Normalize to [0, 1]
    img = np.transpose(img, (2, 0, 1))  # Convert HWC to CHW
    img = np.expand_dims(img, axis=0).astype(np.float32)  # Add batch dimension
    return img, original_shape


# Scale Bounding Boxes
def scale_boxes(boxes, img_shape, original_shape):
    scale_y, scale_x = (
        original_shape[0] / img_shape[0],
        original_shape[1] / img_shape[1],
    )
    boxes[:, [0, 2]] *= scale_x  # Scale x-coordinates
    boxes[:, [1, 3]] *= scale_y  # Scale y-coordinates
    return boxes


# Draw Detections
def draw_detections(image, boxes, confidences):
    for box, conf in zip(boxes, confidences):
        x1, y1, width, height = map(int, box)
        width //= 3
        height //= 3
        label = f"T: {conf:.2f}"
        cv2.rectangle(
            image, (x1 - width, y1 - height), (x1 + width, y1 + height), (0, 255, 0), 2
        )
        cv2.putText(
            image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
        )
    return image


def inference(session, input_details, input_size, confidence_threshold, image):
    # image_path = "data/images/fn.png"  # Path to your input image

    original_image = np.copy(image)
    # Preprocess image
    img, original_shape = preprocess_image(input_size, image=image)

    # Run inference
    input_name = input_details.name

    outputs = session.run(None, {input_name: img})

    # Process outputs

    detections = outputs[0][0]
    boxes = detections[:, :4]  # Bounding boxes
    confidences = detections[:, 4]  # Confidence scores

    # Filter detections by confidence
    valid_indices = confidences > confidence_threshold
    valid_boxes = boxes[valid_indices]
    valid_confidences = confidences[valid_indices]

    # Scale boxes back to original image size
    scaled_boxes = scale_boxes(valid_boxes, input_size, original_shape)

    # Draw detections

    result_image = draw_detections(original_image, scaled_boxes, valid_confidences)
    return result_image, scaled_boxes


# Main Function
def setup():
    model_path = "yolo/models/aimbot_s_3.onnx"  # Path to your ONNX model
    input_size = (640, 640)  # YOLOv5 input size
    confidence_threshold = 0.3  # Minimum confidence to keep detections

    # Load model
    session, input_details = load_model(model_path, "DmlExecutionProvider")
    return session, input_details, input_size, confidence_threshold

    # Display the result


if __name__ == "__main__":
    cam = dxcam.create(output_idx=1)
    cam.start()
    session, input_details, input_size, confidence_threshold = setup()
    while True:
        frame = cam.get_latest_frame()

        new_frame, b = inference(
            session, input_details, input_size, confidence_threshold, frame
        )
        print(b)
        new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
        cv2.imshow("Result", cv2.resize(new_frame, (1280, 720)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cam.stop()
