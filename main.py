import os
from utils import read_video, save_video
from trackers import Tracker
import cv2
import numpy as np
from team_assigner import TeamAssigner
from player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator import CameraMovementEstimator
from view_transformer import ViewTransformer
from speed_and_distance_estimator import SpeedAndDistance_Estimator

# Get absolute paths relative to the script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define absolute paths
INPUT_VIDEOS_DIR = os.path.join(BASE_DIR, 'input_videos')
OUTPUT_VIDEOS_DIR = os.path.join(BASE_DIR, 'output_videos')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
STUBS_DIR = os.path.join(BASE_DIR, 'stubs')

def main():
    # Read Video
    video_frames = read_video(os.path.join(INPUT_VIDEOS_DIR,'08fd33_4.mp4'))
    print("1")
    # Initialize Tracker
    model_path = os.path.join(MODELS_DIR, 'best.pt')
    tracker = Tracker(model_path)
    print("2")

    tracks = tracker.get_object_tracks(video_frames,
                                       read_from_stub=False,stub_path=os.path.join(STUBS_DIR, "track_stubs.pkl")
                                       )
    print("3")
    # Get object positions 
    tracker.add_position_to_tracks(tracks)

    print("4")
    # camera movement estimator
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    print("5")
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(video_frames,
                                                                                read_from_stub=False,stub_path=os.path.join(STUBS_DIR, "camera_movement_stubs.pkl")
                                                                            )
    print("6")
    camera_movement_estimator.add_adjust_positions_to_tracks(tracks,camera_movement_per_frame)

  
    print("7")
    # View Trasnformer
    view_transformer = ViewTransformer()
    print("8")
    view_transformer.add_transformed_position_to_tracks(tracks)

    print("9")
    # Interpolate Ball Positions
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    print("10")
    # Speed and distance estimator
    speed_and_distance_estimator = SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)

    print("11")
    # Assign Player Teams
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], 
                                    tracks['players'][0])
    print("12")
    
    for frame_num, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_num],   
                                                 track['bbox'],
                                                 player_id)
            tracks['players'][frame_num][player_id]['team'] = team 
            tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

    
    print("13")
    # Assign Ball Aquisition
    player_assigner = PlayerBallAssigner()
    team_ball_control= []
    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        else:
            team_ball_control.append(team_ball_control[-1])
    team_ball_control= np.array(team_ball_control)


    print("14")
    # Draw output 
    ## Draw object Tracks
    output_video_frames = tracker.draw_annotations(video_frames, tracks,team_ball_control)
    print("15")

    ## Draw Camera movement
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames,camera_movement_per_frame)
    print("16")

    ## Draw Speed and Distance
    speed_and_distance_estimator.draw_speed_and_distance(output_video_frames,tracks)
    print("17")

    # Save video
    output_video_path = os.path.join(OUTPUT_VIDEOS_DIR, 'output_video.avi')
    save_video(output_video_frames, output_video_path)
    print("18")

if __name__ == '__main__':
    main()