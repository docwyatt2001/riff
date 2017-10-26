import io
import unittest

import riff


class TestStream(unittest.TestCase):
    def test_wraps_bytes(self):
        stream = riff.Stream.from_bytes(b'MOCK')
        self.assertIsInstance(stream, riff.Stream)

    def test_wraps_existing_stream_object(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'MOCK'))
        self.assertIsInstance(stream, riff.Stream)

    def test_existing_stream_object_not_double_wrapped(self):
        base_stream = riff.Stream.from_bytes(b'MOCK')
        stream = riff.Stream.from_stream(base_stream)
        self.assertIs(base_stream, stream)

    def test_tell_returns_base_stream_position(self):
        base_stream = io.BytesIO(b'MOCK')
        base_stream.seek(3)
        stream = riff.Stream.from_stream(base_stream)
        self.assertEqual(3, stream.tell())

    def test_can_read_bytes(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'MOCK'))
        self.assertEqual(b'MOCK', stream.read(4))

    def test_error_reading_truncated_bytes(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'M'))
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            stream.read(4)
        self.assertEqual(
            'Expected 3 more byte(s) after position 1', str(context.exception)
        )

    def test_can_read_fourcc(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'MOCK'))
        self.assertEqual('MOCK', stream.read_fourcc())

    def test_error_reading_truncated_fourcc(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'MO'))
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            stream.read_fourcc()
        self.assertEqual(
            'Expected 2 more byte(s) after position 2', str(context.exception)
        )

    def test_can_read_uint(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'\x04\x00\x00\x00'))
        self.assertEqual(4, stream.read_uint())

    def test_error_reading_truncated_uint(self):
        stream = riff.Stream.from_stream(io.BytesIO(b'\x04\x00\x00'))
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            stream.read_uint()
        self.assertEqual(
            'Expected 1 more byte(s) after position 3', str(context.exception)
        )


class TestRiffChunk(unittest.TestCase):
    def test_chunk_id(self):
        self.assertEqual('RIFF', riff.RiffChunk.ID)

    def test_read_from_stream_with_invalid_chunk_id(self):
        stream = io.BytesIO(b'MOCK\x04\x00\x00\x00LIST')
        with self.assertRaises(riff.ChunkIdInvalid) as context:
            riff.RiffChunk.from_stream(stream)
        self.assertEqual('MOCK != RIFF', str(context.exception))

    def test_read_chunk_id_from_stream(self):
        stream = io.BytesIO(b'RIFF\x04\x00\x00\x00MOCK')
        riff_chunk = riff.RiffChunk.from_stream(stream)
        self.assertEqual('RIFF', riff_chunk.id)

    def test_read_chunk_size_from_stream(self):
        stream = io.BytesIO(b'RIFF\x04\x00\x00\x00MOCK')
        riff_chunk = riff.RiffChunk.from_stream(stream)
        self.assertEqual(4, riff_chunk.size)

    def test_read_riff_format_from_stream(self):
        stream = io.BytesIO(b'RIFF\x04\x00\x00\x00MOCK')
        riff_chunk = riff.RiffChunk.from_stream(stream)
        self.assertEqual('MOCK', riff_chunk.format)

    def test_read_subchunks_from_stream(self):
        stream = io.BytesIO(
            b'RIFF\x20\x00\x00\x00MOCK' +
            b'CK01\x04\x00\x00\x001111' +
            b'CK02\x08\x00\x00\x0022222222'
        )
        riff_chunk = riff.RiffChunk.from_stream(stream)
        self.assertEqual('CK01', riff_chunk.subchunk(0).id)
        self.assertEqual(4, riff_chunk.subchunk(0).size)
        self.assertEqual(b'1111', riff_chunk.subchunk(0).data)
        self.assertEqual('CK02', riff_chunk.subchunk(1).id)
        self.assertEqual(8, riff_chunk.subchunk(1).size)
        self.assertEqual(b'22222222', riff_chunk.subchunk(1).data)

    def test_read_from_stream_with_truncated_chunk_id(self):
        stream = io.BytesIO(b'RIF')
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            riff.RiffChunk.from_stream(stream)
        self.assertEqual(
            'Expected 1 more byte(s) after position 3', str(context.exception)
        )

    def test_read_from_stream_with_truncated_chunk_size(self):
        stream = io.BytesIO(b'RIFF\x04\x00')
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            riff.RiffChunk.from_stream(stream)
        self.assertEqual(
            'Expected 2 more byte(s) after position 6', str(context.exception)
        )

    def test_read_from_stream_with_truncated_riff_data(self):
        stream = io.BytesIO(b'RIFF\x08\x00\x00\x00MOCKDAT')
        with self.assertRaises(riff.UnexpectedEndOfStream) as context:
            riff.RiffChunk.from_stream(stream)
        self.assertEqual(
            'Expected 1 more byte(s) after position 15', str(context.exception)
        )


if __name__ == '__main__':
    unittest.main()
