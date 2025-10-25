import os
import io
from typing import Optional
import azure.cognitiveservices.speech as speechsdk
from fastapi import HTTPException


class AzureSpeechService:
    """
    Service for Azure Speech (Text-to-Speech) integration.
    Converts AI-generated text into audio using Azure Cognitive Services.
    """

    def __init__(self):
        self.speech_config: Optional[speechsdk.SpeechConfig] = None
        self.is_initialized = False
        
    def init_speech_service(self):
        """
        Initialize Azure Speech Service with credentials from environment variables.
        """
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not speech_key:
            print("⚠️  Warning: AZURE_SPEECH_KEY not found. Text-to-speech will be disabled.")
            self.is_initialized = False
            return
        
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=speech_region
            )
            
            # Configure voice settings
            # Default: Vietnamese female voice for D&D narration
            voice_name = os.getenv("AZURE_SPEECH_VOICE", "vi-VN-HoaiMyNeural")
            self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Audio format: MP3 for smaller file size and web compatibility
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
            
            self.is_initialized = True
            print(f"✅ Azure Speech Service initialized (Region: {speech_region}, Voice: {voice_name})")
            
        except Exception as e:
            print(f"❌ Failed to initialize Azure Speech Service: {e}")
            self.is_initialized = False
    
    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Audio bytes in MP3 format
            
        Raises:
            HTTPException: If service is not initialized or conversion fails
        """
        if not self.is_initialized:
            raise HTTPException(
                status_code=503,
                detail="Text-to-speech service is not available. Please configure AZURE_SPEECH_KEY."
            )
        
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        try:
            # Create a pull audio output stream to get audio bytes
            pull_stream = speechsdk.audio.PullAudioOutputStream()
            audio_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
            
            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Synthesize speech
            result = speech_synthesizer.speak_text_async(text).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Read all audio data
                audio_data = bytes(result.audio_data)
                return audio_data
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - Error details: {cancellation_details.error_details}"
                print(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
            
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected synthesis result: {result.reason}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error during text-to-speech conversion: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to convert text to speech: {str(e)}"
            )
    
    async def text_to_speech_with_ssml(self, ssml: str) -> bytes:
        """
        Convert SSML (Speech Synthesis Markup Language) to speech audio.
        This allows more control over speech properties like emphasis, pauses, etc.
        
        Args:
            ssml: SSML formatted text
            
        Returns:
            Audio bytes in MP3 format
            
        Example SSML:
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
                <voice name="vi-VN-HoaiMyNeural">
                    <prosody rate="medium" pitch="medium">
                        You enter a dark dungeon. <break time="500ms"/> 
                        <emphasis level="strong">What do you do?</emphasis>
                    </prosody>
                </voice>
            </speak>
        """
        if not self.is_initialized:
            raise HTTPException(
                status_code=503,
                detail="Text-to-speech service is not available. Please configure AZURE_SPEECH_KEY."
            )
        
        try:
            pull_stream = speechsdk.audio.PullAudioOutputStream()
            audio_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)
            
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return bytes(result.audio_data)
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to synthesize SSML"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"SSML synthesis error: {str(e)}"
            )
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices for the configured region.
        Useful for allowing users to choose their preferred narrator voice.
        
        Returns:
            List of available voice names
        """
        if not self.is_initialized:
            return []
        
        try:
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = speech_synthesizer.get_voices_async().get()
            
            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                return [
                    {
                        "name": voice.short_name,
                        "display_name": voice.local_name,
                        "locale": voice.locale,
                        "gender": voice.gender.name
                    }
                    for voice in result.voices
                ]
            return []
        except Exception as e:
            print(f"❌ Error getting voices: {e}")
            return []


# Global service instance
speech_service = AzureSpeechService()

