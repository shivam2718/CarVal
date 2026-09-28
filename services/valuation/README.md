# Valuation Service

**Owner**: TBD (Suggested for Review 3)

## Overview
Fair market value prediction using machine learning (XGBoost).

## Review 3 Objectives
- Predict fair market value based on vehicle characteristics and damage assessment
- Identify valuation factors and explanations
- Support negotiation insights

## API Contract (Future)

### POST /valuation/predict

Predict vehicle fair value.

**Request:**
```json
{
  "vehicle_data": { /* ... */ },
  "damages": [ /* ... */ ],
  "mileage": 50000
}
```

**Response:**
```json
{
  "predicted_fair_value": 450000,
  "currency": "INR",
  "confidence": 0.87,
  "model": "XGBoost-v1",
  "explanation_factors": [
    {
      "factor": "mileage",
      "impact": -45000,
      "description": "Above average mileage"
    },
    {
      "factor": "damage_assessment",
      "impact": -30000,
      "description": "Minor damages detected"
    }
  ]
}
```

## Status
**Review 2**: Placeholder - `status: "pending"`
