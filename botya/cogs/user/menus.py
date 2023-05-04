import io
import pydub
import discord
import functools
import speech_recognition

from discord import app_commands


@app_commands.context_menu(name="Transcribe voice message")

