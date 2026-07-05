from pyrogram import Client


def get_prefix(client: Client) -> str:
    return client.prefixes[0] if getattr(client, 'prefixes', None) else '.'
