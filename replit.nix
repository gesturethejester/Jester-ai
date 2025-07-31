{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.ffmpeg
    pkgs.streamlink
    pkgs.libffi
    pkgs.openssl
  ];
}
