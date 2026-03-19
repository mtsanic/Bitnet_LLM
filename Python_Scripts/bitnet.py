import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F 
import brevitas.nn as qnn
from brevitas.quant import Int8ActPerTensorFloat
from brevitas.inject.defaults import Int8WeightPerTensorFloat
import os
import warnings

warnings.filterwarnings("ignore", message=".*Named tensors and all their associated APIs.*")
os.makedirs("BitNet_LLM", exist_ok=True)

class BitNetWeightQuant(Int8WeightPerTensorFloat):
    bit_width = 2
    narrow_range = True

class QuantBitNetBlock(nn.Module):
    def __init__(self, hidden_dim=64):
        super(QuantBitNetBlock, self).__init__()
        
        self.quant_in = qnn.QuantIdentity(
            return_quant_tensor=True, 
            act_quant=Int8ActPerTensorFloat
        )
        # FIX: Reverted to bias=False to force a pure 'MatMul' ONNX export
        self.linear1 = qnn.QuantLinear(
            hidden_dim, hidden_dim * 2, 
            bias=False, 
            weight_quant=BitNetWeightQuant,
            return_quant_tensor=True 
        )
        self.relu = qnn.QuantReLU(
            return_quant_tensor=True, 
            act_quant=Int8ActPerTensorFloat
        )
        self.linear2 = qnn.QuantLinear(
            hidden_dim * 2, hidden_dim, 
            bias=False, 
            weight_quant=BitNetWeightQuant,
            return_quant_tensor=False 
        )

    def forward(self, x):
        x = self.quant_in(x)
        x = self.linear1(x)
        x = self.relu(x)
        x = self.linear2(x)
        return x

def train_autoencoder():
    print("\n" + "="*60)
    print("🚀 BITNET 1.58b: HARDWARE-COMPLIANT RECONSTRUCTION")
    print("="*60)
    
    hidden_dim = 64 
    model = QuantBitNetBlock(hidden_dim=hidden_dim)
    model.train()
    
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    N_samples = 10000
    batch_size = 256
    epochs = 400
    
    print(f"[*] Generating structured dataset (Low-Rank Manifold)...")
    rank = 8
    base_patterns = torch.randn(rank, hidden_dim) * 0.5
    coefficients = torch.randn(N_samples, rank)
    
    X_train = torch.matmul(coefficients, base_patterns)
    X_train = X_train / X_train.std() * 0.5
    
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    print(f"[*] Training pure MatMul-Free Autoencoder for {epochs} epochs...\n")
    
    for epoch in range(epochs):
        permutation = torch.randperm(N_samples)
        epoch_loss = 0.0
        
        for i in range(0, N_samples, batch_size):
            indices = permutation[i:i+batch_size]
            batch_x = X_train[indices]
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_x)
            
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        scheduler.step()
        
        if (epoch + 1) % 50 == 0:
            avg_loss = epoch_loss / (N_samples / batch_size)
            print(f"    -> Epoch {epoch+1:3d} | Average MSE Loss: {avg_loss:.6f}")

    print("\n" + "="*60)
    print("⚖️  FINAL HARDWARE ACCURACY CHECK")
    print("="*60)
    
    model.eval()
    test_samples = 500
    
    test_coeffs = torch.randn(test_samples, rank)
    X_test = torch.matmul(test_coeffs, base_patterns)
    X_test = X_test / X_test.std() * 0.5
    
    with torch.no_grad():
        predictions = model(X_test)
        
    similarity = F.cosine_similarity(predictions.flatten(), X_test.flatten(), dim=0).item()
    accuracy_pct = similarity * 100.0
    
    print(f"[*] Tested on {test_samples} unseen structured signals.")
    print(f"[*] Reconstruction Accuracy: {accuracy_pct:.2f}%")
    
    if accuracy_pct >= 90.0:
        print("\n✅ SUCCESS: The 1.58-bit model successfully hit the target.")
    else:
        print("\n⚠️ FAILED: The model is still not converging correctly.")
        
    save_path = "BitNet_LLM/trained_bitnet.pth"
    torch.save(model.state_dict(), save_path)
    print(f"[*] Trained hardware weights safely saved to '{save_path}'")
    print("="*60 + "\n")

if __name__ == "__main__":
    train_autoencoder()