import logging

logger = logging.getLogger(__name__)


async def handle_pumpportal_event(event_type, event):

    if event_type == "new_token":

        logger.info(
            "NEW TOKEN | %s | %s",
            event.get("symbol"),
            event.get("mint")
        )

        # Stage 1 filtering will go here.

    elif event_type == "trade":

        logger.info(
            "TRADE | %s | %s | %s SOL",
            event.get("txType"),
            event.get("mint"),
            event.get("solAmount")
        )

        # Buyer counting and velocity calculations go here.

    elif event_type == "migration":

        logger.info(
            "TOKEN MIGRATED | %s",
            event.get("mint")
        )

        # Migration tracking will go here.
