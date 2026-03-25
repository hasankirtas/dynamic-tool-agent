from typing import Any
from src.tools.abstraction.base_tool import BaseTool, ToolMetadata, ToolParameter


class CurrencyConverterTool(BaseTool):

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="currency_converter",
            description="Convert between fiat currencies and cryptocurrencies using current exchange rates",
            category="finance",
            tags=["currency", "exchange", "crypto", "bitcoin", "forex", "money", "conversion"],
            parameters=[
                ToolParameter(name="amount", type="number", description="Amount to convert"),
                ToolParameter(name="from_currency", type="string", description="Source currency code (e.g. 'USD', 'EUR', 'BTC')"),
                ToolParameter(name="to_currency", type="string", description="Target currency code (e.g. 'TRY', 'ETH', 'GBP')"),
            ],
        )

    def execute(self, **kwargs) -> dict[str, Any]:
        amount = kwargs.get("amount", 0)
        from_curr = kwargs.get("from_currency", "USD")
        to_curr = kwargs.get("to_currency", "EUR")
        mock_rates = {"USD_EUR": 0.92, "USD_TRY": 38.5, "EUR_USD": 1.09, "BTC_USD": 67500, "USD_GBP": 0.79}
        rate_key = f"{from_curr}_{to_curr}"
        rate = mock_rates.get(rate_key, 1.0)
        return {
            "status": "success",
            "from": from_curr,
            "to": to_curr,
            "amount": amount,
            "converted_amount": round(amount * rate, 2),
            "exchange_rate": rate,
        }
