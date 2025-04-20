import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights

# Paths
data_dir = '../dataset'
model_path = 'model.pt'
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Image transforms (smaller resolution = lower memory usage)
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor()
])

# Dataset and DataLoader
dataset = datasets.ImageFolder(data_dir, transform=transform)
train_loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)

# 🧠 Load ResNet18 with weights=None to avoid pretrained overhead
model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(dataset.classes))
model = model.to(device)

# Loss & Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(2):
    model.train()
    total_loss = 0
    for imgs, labels in train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"✅ Epoch {epoch+1} complete | Loss: {total_loss:.4f}")

# Save model
torch.save(model.state_dict(), model_path)
print(f"✅ Model saved to {model_path}")
