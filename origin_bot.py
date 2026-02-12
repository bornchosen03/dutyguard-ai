from __future__ import annotations


class OriginBot:
    """USMCA/FTA helper: Regional Value Content (RVC) calculator.

    MVP uses the Net Cost method:

    $$RVC = \frac{\text{Total} - \text{Non-Originating}}{\text{Total}} \times 100$$

    This is not legal advice.
    """

    def calculate_rvc(self, total_value: float, non_originating_parts_value: float) -> dict:
        if total_value <= 0:
            raise ValueError("total_value must be > 0")
        if non_originating_parts_value < 0:
            raise ValueError("non_originating_parts_value must be >= 0")

        rvc_percentage = ((total_value - non_originating_parts_value) / total_value) * 100

        # USMCA Threshold for many categories is often 60% (varies by rule).
        is_qualified = rvc_percentage >= 60.0

        return {
            "rvc": f"{rvc_percentage:.2f}%",
            "qualified_for_0_duty": is_qualified,
            "action": "Issue USMCA Certificate" if is_qualified else "Pay MFN Duty Rate",
        }


if __name__ == "__main__":
    # --- TEST ---
    bot = OriginBot()
    # $100 total value, $35 of parts from China
    result = bot.calculate_rvc(100, 35)
    print(f"Trade Result: {result}")
