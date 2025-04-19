import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision import models

class WallDefectClassifier:
    def __init__(self, model_path='model.pt', labels=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(pretrained=False)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(labels))
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        self.labels = labels
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])

    def predict(self, image_path):
        image = Image.open(image_path).convert('RGB')
        image = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(image)
            _, predicted = torch.max(outputs, 1)
        return self.labels[predicted.item()]
