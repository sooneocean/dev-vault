---
title: "JSON-RPC 2.0 標準結構"
source: "https://hackmd.io/@jeff377/json-rpc-2-structure"
author:
published:
created: 2026-04-07
description: "JSON-RPC 2.0 是一個輕量級的遠程程序呼叫 (RPC) 協議，使用 JSON 格式作為訊息交換格式。它支持單向呼叫、通知、批次請求及回應，並提供錯誤處理機制。JSON-RPC 2.0 並不限制實作細節，這讓它可以廣泛應用於不同的應用場景。"
tags:
  - "clippings"
---
JSON-RPC 2.0 是一個輕量級的遠程程序呼叫 (RPC) 協議，使用 JSON 格式作為訊息交換格式。它支持單向呼叫、通知、批次請求及回應，並提供錯誤處理機制。JSON-RPC 2.0 並不限制實作細節，這讓它可以廣泛應用於不同的應用場景。

## 訊息結構

每個 JSON-RPC 訊息包含以下基本元素：

### 1\. jsonrpc

- **類型**: 字串
- **描述**: 指定 JSON-RPC 的版本。對於所有 JSON-RPC 2.0 訊息，該字段應設為 `"2.0"` 。

### 2\. method

- **類型**: 字串
- **描述**: 要呼叫的方法名稱。這是處理請求的關鍵。

### 3\. params

- **類型**: 陣列或物件 (可選)
- **描述**: 方法的引數。這個字段是可選的，取決於所呼叫的方法是否需要引數。若方法不需要參數，該字段可省略。

### 4\. id

- **類型**: 整數、字串或 `null`
- **描述**: 用於標識請求的 ID。此 ID 在回應中會返回，以便與請求一一對應。若為通知型請求，該字段可省略。

## JSON-RPC 2.0 訊息類型

JSON-RPC 2.0 支援三種主要訊息類型：Request、Response 和 Error。

### Request 訊息

請求訊息由客戶端發出，要求伺服器執行某個方法。請求訊息必須包含 `jsonrpc` 、 `method` 、 `params` 和 `id` 。

範例：

```json
{
  "jsonrpc": "2.0",
  "method": "subtract",
  "params": [42, 23],
  "id": 1
}
```

- **`method`**: 要呼叫的方法名稱，如 `subtract` 。
- **`params`**: 呼叫方法所需的引數，這裡是 `[42, 23]` 。
- **`id`**: 請求的唯一標識符，這裡是 `1` 。

### Response 訊息

回應訊息由伺服器回傳，表示方法執行的結果。回應訊息包含 `jsonrpc` 、 `result` 和 `id` 。

範例：

```json
{
  "jsonrpc": "2.0",
  "result": 19,
  "id": 1
}
```

- **`result`**: 方法執行的結果，這裡是 `19` 。
- **`id`**: 用來對應請求訊息的 ID。

錯誤訊息由伺服器回傳，表示方法執行過程中出現了錯誤。錯誤訊息包含 `jsonrpc` 、 `error` 和 `id` 。

範例：

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params"
  },
  "id": 1
}
```

- **`error`**: 錯誤訊息，包含錯誤代碼 `code` 和錯誤描述 `message` 。
	- **`code`**: `-32602` 表示參數無效。
		- **`message`**: 錯誤的簡短描述，這裡是 `"Invalid params"` 。
- **`id`**: 用來對應請求訊息的 ID。

## 錯誤處理

當方法執行失敗時，錯誤訊息需要包含以下字段：

### 1\. code

- **類型**: 整數
- **描述**: 錯誤的代碼。標準錯誤代碼可以參考 [JSON-RPC 2.0 錯誤代碼](https://www.jsonrpc.org/specification#error-codes) 定義。

### 2\. message

- **類型**: 字串
- **描述**: 錯誤的簡短描述。

### 3\. data (可選)

- **類型**: 任意
- **描述**: 用於提供附加的錯誤訊息，這是可選的。

## 通知

通知是 JSON-RPC 2.0 的一種特殊請求形式，它不需要 `id` 欄位。這表示客戶端發送請求但不期望回應。

範例：

```json
{
  "jsonrpc": "2.0",
  "method": "sendMessage",
  "params": ["Hello, World!"]
}
```

## 批次請求

JSON-RPC 2.0 允許在一個 HTTP 請求中包含多個 JSON-RPC 請求。這被稱為批次請求。每個請求都會有自己的 `jsonrpc` 、 `method` 、 `params` 和 `id` 。伺服器會對每個請求返回獨立的回應。

範例：

```json
[
  {
    "jsonrpc": "2.0",
    "method": "subtract",
    "params": [42, 23],
    "id": 1
  },
  {
    "jsonrpc": "2.0",
    "method": "add",
    "params": [1, 2],
    "id": 2
  }
]
```

回應：

```json
[
  {
    "jsonrpc": "2.0",
    "result": 19,
    "id": 1
  },
  {
    "jsonrpc": "2.0",
    "result": 3,
    "id": 2
  }
]
```

## 標準錯誤代碼

JSON-RPC 2.0 定義了一些標準的錯誤代碼，這些代碼有助於識別不同類型的錯誤。以下是一些常見的錯誤代碼：

## 小結

JSON-RPC 2.0 是一個靈活且強大的 RPC 協議，廣泛應用於各種分布式系統中。它具有簡單、清晰的結構，可以輕鬆地進行擴展和調整以符合不同的需求。