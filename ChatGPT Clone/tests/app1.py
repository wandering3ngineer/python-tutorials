import flet as ft

async def main(page: ft.Page):
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.appbar = ft.AppBar(title=ft.Text("Audio Recorder"), center_title=True)

    path = "test-audio-file.wav"

    async def handle_start_recording(e):
        print(f"StartRecording: {path}")
        await audio_rec.start_recording_async(path)

    async def handle_stop_recording(e):
        output_path = await audio_rec.stop_recording_async()
        print(f"StopRecording: {output_path}")
        if page.web and output_path is not None:
            await page.launch_url_async(output_path)

    async def handle_list_devices(e):
        devices = await audio_rec.get_input_devices_async()
        print(devices)

    async def handle_has_permission(e):
        try:
            print(f"HasPermission: {await audio_rec.has_permission_async()}")
        except Exception as e:
            print(e)

    async def handle_pause(e):
        print(f"isRecording: {await audio_rec.is_recording_async()}")
        if await audio_rec.is_recording_async():
            await audio_rec.pause_recording_async()

    async def handle_resume(e):
        print(f"isPaused: {await audio_rec.is_paused_async()}")
        if await audio_rec.is_paused_async():
            await audio_rec.resume_recording_async()

    async def handle_audio_encoding_test(e):
        for i in list(ft.AudioEncoder):
            print(f"{i}: {await audio_rec.is_supported_encoder_async(i)}")

    async def handle_state_change(e):
        print(f"State Changed: {e.data}")

    # Define a function to play the audio
    def play_audio(e):
        audio1.play()

    # Define a function to stop the audio
    def stop_audio(e):
        audio1.pause()

    audio_rec = ft.AudioRecorder(
        audio_encoder=ft.AudioEncoder.WAV,
        on_state_changed=handle_state_change,
    )
    audio1 = ft.Audio(
        src="https://luan.xyz/files/audio/ambient_c_motion.mp3", autoplay=False
    ) 
    page.overlay.append(audio_rec)
    page.overlay.append(audio1)
    await page.update_async()

    await page.add_async(
        ft.ElevatedButton("Start Audio Recorder", on_click=handle_start_recording),
        ft.ElevatedButton("Stop Audio Recorder", on_click=handle_stop_recording),
        ft.ElevatedButton("List Devices", on_click=handle_list_devices),
        ft.ElevatedButton("Pause Recording", on_click=handle_pause),
        ft.ElevatedButton("Resume Recording", on_click=handle_resume),
        ft.ElevatedButton("Test AudioEncodings", on_click=handle_audio_encoding_test),
        ft.ElevatedButton("Has Permission", on_click=handle_has_permission),
        ft.ElevatedButton("Start playing", on_click=play_audio),
        ft.ElevatedButton("Stop playing", on_click=stop_audio)
    )


ft.app(target=main)

# Build with
# flet build web --include-packages flet_audio flet_audio_recorder