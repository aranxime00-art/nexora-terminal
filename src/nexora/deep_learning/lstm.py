from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim


class SimpleLSTM(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 1, output_size: int = 1) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.lstm(x, (h0, c0))
        # Solo predecimos el último paso de la secuencia
        out = self.fc(out[:, -1, :])
        return out

def create_sequences(data: np.ndarray, seq_length: int) -> tuple[np.ndarray, np.ndarray]:
    """Convierte un array 1D en secuencias (X) y objetivos (y)."""
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        y = data[i + seq_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

def train_lstm_model(returns: pd.Series, seq_length: int = 10, epochs: int = 10) -> dict[str, Any]:
    """
    Entrena una red LSTM para predecir el retorno del día siguiente
    basándose en una secuencia de días anteriores.
    """
    # Preparar datos
    data = returns.dropna().values.astype(np.float32)
    if len(data) < seq_length + 10:
        return {"error": "Not enough data"}

    X, y = create_sequences(data, seq_length)

    # Convertir a tensores de PyTorch (Shape: [batch, seq_length, features=1])
    X_tensor = torch.from_numpy(X).unsqueeze(-1)
    y_tensor = torch.from_numpy(y).unsqueeze(-1)

    # Instanciar modelo
    model = SimpleLSTM(input_size=1, hidden_size=16, num_layers=1, output_size=1)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # Bucle de entrenamiento
    model.train()
    final_loss = 0.0
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        loss.backward()
        optimizer.step()
        final_loss = loss.item()

    return {
        "model": "LSTM",
        "final_loss": final_loss,
        "epochs": epochs,
        "samples": len(X)
    }
