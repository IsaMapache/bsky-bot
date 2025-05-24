#!/usr/bin/env python3
"""
Test script to demonstrate TextBuilder functionality for rich text posts.
This shows how the links will be made clickable in Bluesky posts.
"""

try:
    from atproto import client_utils
    ATPROTO_AVAILABLE = True
except ImportError:
    ATPROTO_AVAILABLE = False
    print("⚠️  atproto library not installed - showing fallback behavior")

def test_text_builder():
    """Test TextBuilder functionality."""
    if not ATPROTO_AVAILABLE:
        print("Install atproto with: pip install atproto")
        return
    
    print("🧪 Testing TextBuilder for clickable links...")
    
    # Create a TextBuilder instance like our updated code does
    text_builder = client_utils.TextBuilder()
    
    # Build the same content as post_live_notification
    text_builder.text("🔴 I'm live on Twitch rn come slide!~\n\n")
    text_builder.text("📺 Testing Stream\n\n🎮 Playing Just Chatting\n\n")
    text_builder.tag("#blacksygamers", "blacksygamers").text(" ")
    text_builder.tag("#gaming", "gaming").text(" ")
    text_builder.tag("#twitch", "twitch").text(" ")
    text_builder.tag("#streaming", "streaming").text("\n\n")
    text_builder.link("https://twitch.tv/testuser", "https://twitch.tv/testuser")
    
    # Show the built text
    print("📝 Built text:")
    print(text_builder.build_text())
    
    print("\n🔗 Built facets (link metadata):")
    facets = text_builder.build_facets()
    for i, facet in enumerate(facets):
        print(f"  Facet {i+1}: {facet}")
        
    print("\n✅ When posted to Bluesky, hashtags and the URL will be clickable links!")

if __name__ == "__main__":
    test_text_builder() 